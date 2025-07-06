import random  # For randomizing election timeouts
from concurrent import futures
import grpc
import warnings
warnings.filterwarnings("ignore", message="Protobuf gencode version.*")
import threading
import login_pb2
import login_pb2_grpc
import hashlib
import os
import mysql.connector
import time
import json
import logging
import sys
import base64

# Custom filter to add missing fields like 'node_id' if they are not present
class NodeIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'node_id'):
            record.node_id = 'N/A'  # Default value if 'node_id' is not provided
        return True

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [Node %(node_id)s]: %(message)s',
    style='%',
    
)

# Add the custom filter to the root logger
logging.getLogger().addFilter(NodeIDFilter())

# Token expiration time
TOKEN_EXPIRY = 300  # 300 seconds token expiration.

# MySQL database connection
db_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="userpassword",
    database="LMSDatabase"
)

# Clear unread results
def clear_results():
    # Ensure the connection is cleared of any unread results before executing a new query
    try:
        while db_conn.unread_result:
            db_conn.get_rows()
    except Exception as e:
        print(f"Error clearing unread results: {e}", exc_info=True)

# Function to retrieve session from the database
def get_session(token):
    cursor = db_conn.cursor()
    try:
        cursor.execute("SELECT UserId, UserType, Expiry FROM Sessions WHERE Token = %s", (token,))
        result = cursor.fetchone()
        if result:
            user_id, user_type, expiry = result
            expiry_timestamp = expiry.timestamp()
            if time.time() < expiry_timestamp:
                return {'UserId': str(user_id), 'UserType': user_type, 'expiry': expiry_timestamp}
            else:
                # Session expired, delete it
                cursor.execute("DELETE FROM Sessions WHERE Token = %s", (token,))
                db_conn.commit()
        else:
            cursor.fetchall()
        return None
    finally:
        cursor.close()

# LogEntry class for the Raft log
class LogEntry:
    def __init__(self, term, command):
        self.term = term
        self.command = command  # Command is a JSON string

# Class for RaftNode
class RaftNode(login_pb2_grpc.RaftServicer):
    def __init__(self, node_id, followers,node_address):
        self.node_id = node_id
        self.node_address=node_address
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'node_id': self.node_id})
        self.current_term = 0
        self.voted_for = None
        self.log = []  # List of LogEntry objects
        self.commit_index = -1
        self.last_applied = -1
        self.state = 'follower'
        self.followers = followers  # List of follower addresses
        self.follower_failures = {follower: 0 for follower in followers}
        self.followers_lock = threading.Lock()
        self.leader_id = None
        self.leader_address=None
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(5, 10)  # Randomized election timeout
        self.heartbeat_interval = 1  # Shortened interval for faster replication
        self.majority = (len(followers) + 1) // 2 + 1  # Include self in majority calculation
        self.next_index = {}
        self.match_index = {}
        self.commit_index_lock = threading.Lock()
        threading.Thread(target=self.election_timeout_handler, daemon=True).start()

    def RequestVote(self, request, context):
        candidate_term = request.term
        candidate_id = request.candidateId

        if candidate_term > self.current_term:
            self.logger.info(f"Updating term from {self.current_term} to {candidate_term}")
            self.current_term = candidate_term
            self.voted_for = None
            self.state = 'follower'

        vote_granted = False
        if self.current_term == candidate_term and (self.voted_for is None or self.voted_for == candidate_id):
            vote_granted = True
            self.voted_for = candidate_id

        if vote_granted:
            self.logger.info(f"Voted for candidate {candidate_id} in term {candidate_term}")

        return login_pb2.RequestVoteReply(term=self.current_term, vote_granted=vote_granted)

    def AppendEntries(self, request, context):
        leader_term = request.term
        leader_id = request.leaderId
        prev_log_index = request.prevLogIndex
        prev_log_term = request.prevLogTerm
        leader_commit = request.leaderCommit
        self.leader_address=request.leaderAddress  #store leader's address

        if leader_term < self.current_term:
            return login_pb2.AppendEntriesReply(term=self.current_term, success=False)

        if leader_term > self.current_term:
            self.logger.info(f"Updating term from {self.current_term} to {leader_term}")
            self.current_term = leader_term
            self.voted_for = None

        self.leader_id = leader_id
        if self.state != 'follower':
            self.logger.info(f"Becoming follower under leader {self.leader_id}")
        self.state = 'follower'
        self.last_heartbeat = time.time()

        entries = [LogEntry(entry.term, entry.command) for entry in request.entries]

        # Check for log consistency
        if prev_log_index >= 0:
            if prev_log_index >= len(self.log) or self.log[prev_log_index].term != prev_log_term:
                return login_pb2.AppendEntriesReply(term=self.current_term, success=False)

        # Append any new entries not already in the log
        with threading.Lock():
            self.log = self.log[:prev_log_index + 1]
            self.log.extend(entries)

        # Update commit index
        if leader_commit > self.commit_index:
            with self.commit_index_lock:
                self.commit_index = min(leader_commit, len(self.log) - 1)
            self.apply_log_entries()

        return login_pb2.AppendEntriesReply(term=self.current_term, success=True)

    def election_timeout_handler(self):
        while True:
            time.sleep(0.5)  # Check more frequently
            if time.time() - self.last_heartbeat > self.election_timeout and self.state != 'leader':
                self.logger.info("Election timeout, starting election")
                self.start_election()
                # Randomize the election timeout after each election
                self.election_timeout = random.uniform(5, 10)

    def start_election(self):
        self.state = 'candidate'
        self.current_term += 1
        self.voted_for = self.node_id
        self.logger.info(f"Starting election for term {self.current_term}")

        votes = 1  # Vote for self
        for follower in self.followers:
            response = self.request_vote_rpc(follower)
            if response:
                if response.term > self.current_term:
                    self.logger.info(f"Found higher term {response.term} from {follower}, stepping down")
                    self.current_term = response.term
                    self.voted_for = None
                    self.state = 'follower'
                    return
                if response.vote_granted:
                    votes += 1

        if votes >= self.majority:
            self.state = 'leader'
            self.logger.info(f"Became leader for term {self.current_term}")
            # Initialize nextIndex and matchIndex for each follower
            for follower in self.followers:
                self.next_index[follower] = len(self.log)
                self.match_index[follower] = -1
            # Start per-follower replication threads
            for follower in self.followers:
                threading.Thread(target=self.replicate_log_entries, args=(follower,), daemon=True).start()
        else:
            self.state = 'follower'
            self.logger.info(f"Failed to become leader in term {self.current_term}, received {votes} votes")

    def request_vote_rpc(self, follower_address):
        try:
            with grpc.insecure_channel(follower_address) as channel:
                stub = login_pb2_grpc.RaftStub(channel)
                request = login_pb2.RequestVoteRequest(term=int(self.current_term), candidateId=str(self.node_id))
                response = stub.RequestVote(request, timeout=5)  # Set a timeout
                return response
        except grpc.RpcError as e:
            self.logger.debug(f"Error requesting vote from {follower_address}: {e.details()}")
            return None

    def replicate_log_entries(self, follower_address):
        # Initialize nextIndex and matchIndex if not present
        if follower_address not in self.next_index:
            self.next_index[follower_address] = len(self.log)
        if follower_address not in self.match_index:
            self.match_index[follower_address] = -1

        while self.state == 'leader':
            prev_log_index = self.next_index[follower_address] - 1
            prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 else 0

            entries = []
            with threading.Lock():
                if self.next_index[follower_address] < len(self.log):
                    entries = self.log[self.next_index[follower_address]:]

            entries_proto = [
                login_pb2.LogEntry(term=entry.term, command=entry.command)
                for entry in entries
            ]

            request = login_pb2.AppendEntriesRequest(
                term=self.current_term,
                leaderId=str(self.node_id),
                prevLogIndex=prev_log_index,
                prevLogTerm=prev_log_term,
                entries=entries_proto,
                leaderCommit=self.commit_index,
                leaderAddress=self.node_address
            )

            try:
                with grpc.insecure_channel(follower_address) as channel:
                    stub = login_pb2_grpc.RaftStub(channel)
                    response = stub.AppendEntries(request, timeout=1)
                    if response.term > self.current_term:
                        self.logger.info(f"Discovered higher term {response.term} from {follower_address}, stepping down")
                        self.current_term = response.term
                        self.state = 'follower'
                        self.voted_for = None
                        return
                    if response.success:
                        if entries:
                            self.logger.info(f"Replication successful to follower {follower_address} for log index {self.next_index[follower_address]}")

                            self.match_index[follower_address] = self.next_index[follower_address] + len(entries) - 1
                            self.next_index[follower_address] = self.match_index[follower_address] + 1
                            # Advance commit index if a majority has replicated an entry
                            self.update_commit_index()
                        else:
                            self.logger.info(f"Heartbeat successful to follower {follower_address}")
                            # Heartbeat successful
                            
                            pass
                    else:
                        self.logger.warning(f"Replication failed for follower {follower_address}, decrementing nextIndex")

                        self.next_index[follower_address] = max(0, self.next_index[follower_address] - 1)
            except grpc.RpcError as e:
                self.logger.debug(f"Error replicating log to {follower_address}: {e.details()}")

            time.sleep(self.heartbeat_interval)

    def update_commit_index(self):
        with self.commit_index_lock:
            for N in range(len(self.log) - 1, self.commit_index, -1):
                count = 1  # Start with self
                for follower in self.followers:
                    if self.match_index.get(follower, -1) >= N:
                        count += 1
                if count >= self.majority and self.log[N].term == self.current_term:
                    self.logger.info(f"Committing log entry {N} on leader")
                    self.commit_index = N
                    self.apply_log_entries()
                    break

    def apply_log_entries(self):
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            self.logger.info(f"Applying log entry {self.last_applied} on node {self.node_id}")
            self.apply(entry.command)

    def apply(self, command_json):
        try:
            command = json.loads(command_json)
            operation = command['operation']
            data = command['data']

            if operation == 'UploadAssignment':
                student_id = data['student_id']
                assignment_data_str = data['assignment_data_str']
                assignment_data = base64.b64decode(assignment_data_str.encode('utf-8'))  # Convert back to bytes
                file_path = f'uploads/{student_id}_assignment.pdf'

                # Ensure the uploads directory exists
                os.makedirs('uploads', exist_ok=True)

                # Write the assignment file
                try:
                    with open(file_path, 'wb') as f:
                        f.write(assignment_data)
                except Exception as e:
                    self.logger.error(f"Error writing assignment file for student {student_id}: {e}", exc_info=True)
                    return

                # Database operation
                cursor = db_conn.cursor()
                try:
                    cursor.execute("INSERT INTO Assignment (StudentId, FilePath) VALUES (%s, %s)", (student_id, file_path))
                    db_conn.commit()
                except mysql.connector.Error as err:
                    self.logger.error(f"MySQL error: {err}", exc_info=True)
                finally:
                    cursor.close()
            elif operation == 'GradeAssignment':
                assignment_id = data['assignment_id']
                student_id=data['student_id']
                grade = data['grade']
                feedback = data['feedback']
                self.logger.info(f"Applying grade assignment {student_id} with grade {grade}")
                try:
                    cursor = db_conn.cursor()
                    cursor.execute("""
                        UPDATE Assignment 
                        SET Grade = %s, Feedback = %s, GradingStatus = 1, FeedbackStatus = 1 
                        WHERE StudentId = %s
                    """, (grade, feedback, student_id))
                    db_conn.commit()
                except mysql.connector.Error as err:
                    self.logger.error(f"MySQL error: {err}", exc_info=True)
                finally:
                    cursor.close()
            elif operation == 'PostQuery':
                student_id = data['student_id']
                title = data['title']
                body = data['body']
                cursor = db_conn.cursor()
                try:
                    cursor.execute("SELECT QueryId FROM Query WHERE StudentId = %s", (student_id,))
                    existing_query = cursor.fetchone()
                    if existing_query:
                        cursor.execute("""
                            UPDATE Query 
                            SET Title = %s, Body = %s, Status = 0, Reply = NULL
                            WHERE QueryId = %s
                        """, (title, body, existing_query[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO Query (StudentId, Title, Body, Status)
                            VALUES (%s, %s, %s, 0)
                        """, (student_id, title, body))
                    db_conn.commit()
                except mysql.connector.Error as err:
                    self.logger.error(f"MySQL error: {err}", exc_info=True)
                finally:
                    cursor.close()
            elif operation == 'ReplyToQuery':
                student_id=data['student_id']
                reply = data['reply']
                query_id = data['query_id']
                self.logger.info(f"Applying query reply {student_id} with reply {reply}")
                try:
                    cursor = db_conn.cursor()
                    
                    cursor.execute("UPDATE Query SET Reply = %s, Status = 1 WHERE StudentId = %s", (reply, student_id))
                    db_conn.commit()
                except mysql.connector.Error as err:
                    self.logger.error(f"MySQL error: {err}", exc_info=True)
                finally:
                    cursor.close()
            elif operation == 'UploadCourseMaterial':
                title = data['title']
                material_data_str = data['material_data']
                material_data = base64.b64decode(material_data_str.encode('utf-8'))
                uploaded_by = data['uploaded_by']
                file_path = f'uploads/course_materials/{title}.pdf'
                os.makedirs('uploads/course_materials', exist_ok=True)
                try:
                    with open(file_path, 'wb') as f:
                        f.write(material_data)
                except Exception as e:
                    self.logger.error(f"Error writing course material {title}: {e}", exc_info=True)
                    return
                cursor = db_conn.cursor()
                try:
                    cursor.execute("INSERT INTO CourseMaterials (DocId, Title, FilePath, UploadedBy) VALUES (%s, %s, %s, %s)",
                                   (title, title, file_path, uploaded_by))
                    db_conn.commit()
                except mysql.connector.Error as err:
                    self.logger.error(f"MySQL error: {err}", exc_info=True)
                finally:
                    cursor.close()
            # Handle other operations similarly
        except Exception as e:
            self.logger.error(f"Error applying command: {e}", exc_info=True)

    def append_entry(self, command):
        if self.state != 'leader':
            return None

        # Serialize the command to JSON
        command_json = json.dumps(command)

        entry = LogEntry(self.current_term, command_json)
        with threading.Lock():
            self.log.append(entry)
            index = len(self.log) - 1

        # Note: Replication is handled by the per-follower threads
        return index

    # Method to get log entries (if needed)
    # def GetLogEntries(self, request, context):
    #     entries_proto = [
    #         login_pb2.LogEntry(term=entry.term, command=entry.command)
    #         for entry in self.log
    #     ]
    #     return login_pb2.GetLogEntriesResponse(entries=entries_proto)

# LMSService class
class LMSService(login_pb2_grpc.LMSServicer):
    def __init__(self, raft_node):
        self.raft_node = raft_node
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'node_id': self.raft_node.node_id})

    # Login function
    def Login(self, request, context):
        clear_results()
        cursor = db_conn.cursor()
        try:
            hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
            cursor.execute("SELECT UserId, UserType FROM Users WHERE Username = %s AND Password = %s", (request.username, hashed_password))
            user = cursor.fetchone()

            if user:
                token = hashlib.sha256(os.urandom(16)).hexdigest()
                expiry = time.time() + TOKEN_EXPIRY
                expiry_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry))
                # Ensure UserId is a string
                user_id = str(user[0])
                # Store session in the database
                cursor.execute(
                    "INSERT INTO Sessions (Token, UserId, UserType, Expiry) VALUES (%s, %s, %s, %s)",
                    (token, user_id, user[1], expiry_time)
                )
                db_conn.commit()
                return login_pb2.LoginResponse(token=token, message="Login successful", user_type=user[1])
            else:
                return login_pb2.LoginResponse(token="", message="Login failed", user_type="")
        finally:
            cursor.close()

    # Check if the student has uploaded an assignment
    def CheckAssignmentStatus(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            student_id = session['UserId']
            cursor = db_conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM Assignment WHERE StudentId = %s", (student_id,))
                result = cursor.fetchone()
                uploaded = result[0] > 0  # True if the student has uploaded an assignment
                return login_pb2.AssignmentStatusResponse(uploaded=uploaded)
            finally:
                cursor.close()
        else:
            return login_pb2.AssignmentStatusResponse(uploaded=False)

    # Upload assignment
    def UploadAssignment(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            if self.raft_node.state != 'leader':
                # Return an error indicating who the leader is
                leader_address = self.raft_node.leader_address
                context.abort(grpc.StatusCode.UNAVAILABLE, f"Not the leader. Leader is at {leader_address}")

            student_id = session['UserId']
            assignment_data_bytes = request.assignment_data
            assignment_data_str = base64.b64encode(assignment_data_bytes).decode('utf-8') # Convert bytes to string
            
            # Prepare the command
            command = {
                'operation': 'UploadAssignment',
                'data': {
                    'student_id': student_id,
                    'assignment_data_str': assignment_data_str 
                }
            }

            # Append the command to the Raft log
            index = self.raft_node.append_entry(command)

            if index is None:
                context.abort(grpc.StatusCode.UNAVAILABLE, "Not the leader. Please try again.")

            # Wait until the entry is committed
            while self.raft_node.commit_index < index:
                time.sleep(0.5)

            return login_pb2.AssignmentUploadResponse(message="Assignment uploaded successfully.")
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

    # Check feedback and grade
    def CheckFeedback(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            student_id = session['UserId']
            cursor = db_conn.cursor()
            try:
                cursor.execute("SELECT GradingStatus, FeedbackStatus, Feedback, Grade FROM Assignment WHERE StudentId = %s", (student_id,))
                result = cursor.fetchone()
                if result:
                    grading_status = result[0]  # 1 if graded, 0 otherwise
                    feedback_status = result[1]  # 1 if feedback provided, 0 otherwise
                    feedback = result[2] if feedback_status else "No feedback provided yet."
                    grade = result[3] if grading_status else "Not graded yet."
                    cursor.fetchall()
                    return login_pb2.FeedbackResponse(
                        feedback=feedback,
                        graded=bool(grading_status),
                        grade=grade
                    )
                else:
                    return login_pb2.FeedbackResponse(
                        feedback="No assignment found.",
                        graded=False,
                        grade="N/A"
                    )
            finally:
                cursor.close()
        else:
            return login_pb2.FeedbackResponse(
                feedback="Invalid or expired token.",
                graded=False,
                grade="N/A"
            )

    # Fetch ungraded assignments for instructor
    def ViewUngradedAssignments(self, request, context):
        clear_results()
        session = get_session(request.token)

        if session and session['expiry'] > time.time() and session['UserType'] == 'instructor':
            cursor = db_conn.cursor()
            try:
                # Get all ungraded assignments (GradingStatus = 0)
                cursor.execute("SELECT AssignmentId, StudentId, FilePath FROM Assignment WHERE GradingStatus = 0")
                assignments = cursor.fetchall()

                assignment_list = []
                for assignment in assignments:
                    assignment_list.append(login_pb2.Assignment(
                        assignment_id=assignment[0],
                        student_id=assignment[1],
                        file_path=assignment[2]
                    ))

                return login_pb2.ViewUngradedAssignmentsResponse(assignments=assignment_list)
            except mysql.connector.Error as err:
                self.logger.error(f"MySQL error: {err}", exc_info=True)
                return login_pb2.ViewUngradedAssignmentsResponse(assignments=[])
            finally:
                cursor.close()
        else:
            return login_pb2.ViewUngradedAssignmentsResponse(assignments=[])

    # Grade assignment and provide feedback
    def GradeAssignment(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time() and session['UserType'] == 'instructor':
            if self.raft_node.state != 'leader':
                # Return an error indicating who the leader is
                leader_address = self.raft_node.leader_address
                context.abort(grpc.StatusCode.UNAVAILABLE, f"Not the leader. Leader is at {leader_address}")

            # Prepare the command
            command = {
                'operation': 'GradeAssignment',
                'data': {
                    'assignment_id': request.assignment_id,
                    'grade': request.grade,
                    'feedback': request.feedback,
                    'student_id':request.student_id
                }
            }

            # Append the command to the Raft log
            index = self.raft_node.append_entry(command)

            if index is None:
                context.abort(grpc.StatusCode.UNAVAILABLE, "Not the leader. Please try again.")

            # Wait until the entry is committed
            while self.raft_node.commit_index < index:
                time.sleep(0.5)

            return login_pb2.GradeAssignmentResponse(message="Assignment graded successfully.")
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

    # Post a query
    def PostQuery(self, request, context):
        clear_results()
        session = get_session(request.token)

        if session and session['expiry'] > time.time():
            if self.raft_node.state != 'leader':
                leader_address = self.raft_node.leader_address
                context.abort(grpc.StatusCode.UNAVAILABLE, f"Not the leader. Leader is at {leader_address}")

            student_id = session['UserId']

            # Prepare the command
            command = {
                'operation': 'PostQuery',
                'data': {
                    'student_id': student_id,
                    'title': request.title,
                    'body': request.query
                }
            }

            # Append the command to the Raft log
            index = self.raft_node.append_entry(command)

            if index is None:
                context.abort(grpc.StatusCode.UNAVAILABLE, "Not the leader. Please try again.")

            # Wait until the entry is committed
            while self.raft_node.commit_index < index:
                time.sleep(0.1)

            return login_pb2.QueryResponse(message="Query posted successfully.")
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")
    
    
    def AskQuestion(self, request, context):
        clear_results()  # Clear any unread results before starting the new query
        session = get_session(request.token)
        
        if session and session['expiry'] > time.time():
            student_id = session['UserId']
            question=request.question
            print(f"Received question from student:{question}")
            
            with grpc.insecure_channel('192.168.228.79:50010') as channel:
                self.stub = login_pb2_grpc.LMSStub(channel)
                request=login_pb2.AnswerRequest(question=question)
                response=self.stub.GenerateAnswer(request)
                return login_pb2.AnswerResponse(answer=response.answer)
            
               
        else:
            print("Invalid or expired token.")
            return login_pb2.QueryResponse(message="Invalid or expired token.")
    
    
    
    
    # Check query reply
    def CheckQueryReply(self, request, context):
        clear_results()
        session = get_session(request.token)

        if session and session['expiry'] > time.time():
            student_id = session['UserId']
            cursor = db_conn.cursor()

            try:
                cursor.execute("SELECT Reply FROM Query WHERE StudentId = %s AND Status = 1", (student_id,))
                result = cursor.fetchone()

                if result:
                    if result[0]:
                        return login_pb2.CheckQueryReplyResponse(reply=result[0])
                    else:
                        return login_pb2.CheckQueryReplyResponse(reply="No reply found for your query.")
                else:
                    return login_pb2.CheckQueryReplyResponse(reply="Query not replied yet.")
            except mysql.connector.Error as err:
                self.logger.error(f"MySQL error: {err}", exc_info=True)
                return login_pb2.CheckQueryReplyResponse(reply="Error retrieving query reply.")
            finally:
                cursor.close()
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

    # View queries for the instructor
    def ViewQueries(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time() and session['UserType'] == 'instructor':
            cursor = db_conn.cursor()
            try:
                cursor.execute("SELECT QueryId,StudentId, Title, Body FROM Query WHERE Status = 0")
                queries = cursor.fetchall()

                query_list = []
                for query in queries:
                    query_list.append(login_pb2.Query(
                        query_id=query[0],
                        student_id=query[1],
                        title=query[2],
                        body=query[3]
                    ))

                return login_pb2.QueryViewResponse(queries=query_list)
            finally:
                cursor.close()
        else:
            return login_pb2.QueryViewResponse(queries=[])

    # Reply to a query by instructor
    def ReplyToQuery(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time() and session['UserType'] == 'instructor':
            if self.raft_node.state != 'leader':
                leader_address = self.raft_node.leader_address
                context.abort(grpc.StatusCode.UNAVAILABLE, f"Not the leader. Leader is at {leader_address}")
            
            username=session['UserId']
            # Prepare the command
            command = {
                'operation': 'ReplyToQuery',
                'data': {
                    'reply': request.reply,
                    'query_id': request.query_id,
                    'username': username,
                    'student_id':request.student_id
                }
            }

            # Append the command to the Raft log
            index = self.raft_node.append_entry(command)

            if index is None:
                context.abort(grpc.StatusCode.UNAVAILABLE, "Not the leader. Please try again.")

            # Wait until the entry is committed
            while self.raft_node.commit_index < index:
                time.sleep(0.1)

            return login_pb2.ReplyToQueryResponse(message="Reply sent successfully.")
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

    # Upload course material
    def UploadCourseMaterial(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time() and session['UserType'] == 'instructor':
            if self.raft_node.state != 'leader':
                leader_address = self.raft_node.leader_address
                context.abort(grpc.StatusCode.UNAVAILABLE, f"Not the leader. Leader is at {leader_address}")

            material_data_bytes = request.material_data
             
            material_data_str = base64.b64encode(material_data_bytes).decode('utf-8')

            # Prepare the command
            command = {
                'operation': 'UploadCourseMaterial',
                'data': {
                    'material_data': material_data_str,
                    'title': request.title,
                    'uploaded_by': session['UserId']
                }
            }

            # Append the command to the Raft log
            index = self.raft_node.append_entry(command)

            if index is None:
                context.abort(grpc.StatusCode.UNAVAILABLE, "Not the leader. Please try again.")

            # Wait until the entry is committed
            while self.raft_node.commit_index < index:
                time.sleep(0.1)

            return login_pb2.CourseMaterialUploadResponse(message="Course material uploaded successfully.")
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

    # List course materials
    def ListCourseMaterials(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            cursor = db_conn.cursor()
            try:
                cursor.execute("SELECT Title FROM CourseMaterials")
                materials = cursor.fetchall()

                response = login_pb2.CourseMaterialListResponse()
                for material in materials:
                    response.titles.append(material[0])
                return response
            finally:
                cursor.close()
        else:
            return login_pb2.CourseMaterialListResponse()

    # Download course material
    def DownloadCourseMaterial(self, request, context):
        clear_results()
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            cursor = db_conn.cursor()
            try:
                cursor.execute("SELECT FilePath FROM CourseMaterials WHERE Title = %s", (request.title,))
                material = cursor.fetchone()

                if material:
                    file_path = material[0]
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    return login_pb2.CourseMaterialDownloadResponse(content=content, message="Download successful.")
                else:
                    return login_pb2.CourseMaterialDownloadResponse(message="Course material not found.")
            finally:
                cursor.close()
        else:
            return login_pb2.CourseMaterialDownloadResponse(message="Invalid or expired token.")

    # Validate token
    def ValidateToken(self, request, context):
        session = get_session(request.token)
        if session and session['expiry'] > time.time():
            return login_pb2.ValidateTokenResponse(valid=True)
        else:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

# gRPC server setup

def serve(node_id, node_address, all_node_addresses):
    followers = [address for address in all_node_addresses if address != node_address]

    raft_node = RaftNode(node_id, followers, node_address)
    lms_service = LMSService(raft_node)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register RaftNode for Raft gRPC services
    login_pb2_grpc.add_RaftServicer_to_server(raft_node, server)

    # Register LMSService for LMS-related gRPC services
    login_pb2_grpc.add_LMSServicer_to_server(lms_service, server)

    # Bind server to the node address directly (which already includes the port)
    server.add_insecure_port(node_address)
    server.start()
    print(f"Server started on {node_address}.")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nGracefully stopping the server...")
        server.stop(grace=1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python server.py <node_id> <node_address> <other_node_address1> <other_node_address2> ...")
        sys.exit(1)

    node_id = int(sys.argv[1])
    node_address = sys.argv[2]
    other_node_addresses = sys.argv[3:]

    all_node_addresses = [node_address] + other_node_addresses
    serve(node_id, node_address, all_node_addresses)