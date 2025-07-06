import sys
import grpc
import warnings
warnings.filterwarnings("ignore", message="Protobuf gencode version.*")
import login_pb2
import login_pb2_grpc
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename


os.environ['TK_SILENCE_DEPRECATION'] = '1'


class InstructorClient:
    def __init__(self, server_addresses):
        self.server_addresses = server_addresses  # List of server addresses
        self.current_server_index = 0
        self.leader_address = self.server_addresses[0]  #start with the first server address
        self.token = None

    def send_request(self, request_func_name, request):
        """Send request to the leader and handle any failures."""
        retries = 0
        max_retries = len(self.server_addresses)
        while retries < max_retries:
            server_address = self.leader_address
            try:
                with grpc.insecure_channel(server_address) as channel:
                    stub = login_pb2_grpc.LMSStub(channel)
                    request_func = getattr(stub, request_func_name)
                    response = request_func(request)
                    return response, None
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    details = e.details()
                    if details and "Leader is at" in details:
                        leader_address = details.split("Leader is at ")[1].strip()
                        print(f"Redirected to leader at {leader_address}")
                        self.leader_address = leader_address
                        retries += 1
                    else:
                        print(f"Server {server_address} unavailable.")
                        # Try next server
                        retries += 1
                        self.current_server_index = (self.current_server_index + 1) % len(self.server_addresses)
                        self.leader_address = self.server_addresses[self.current_server_index]
                else:
                    print(f"gRPC Error from server {server_address}: {e.details()}")
                    return None, e
        print("All servers are unavailable. Please try again later.")
        return None, grpc.RpcError("All servers are unavailable.")

    def login(self):
        while True:
            username = input("Enter username: ")
            password = input("Enter password: ")
            request = login_pb2.LoginRequest(username=username, password=password)
            response, error = self.send_request('Login', request)

            if response:
                if response.token:
                    if response.user_type == "instructor":  # Ensure it's an instructor
                        print(f"Login successful! Token: {response.token}")
                        self.token = response.token
                        return True
                    else:
                        print("Error: This login is only for instructors.")
                else:
                    print("Login failed. Please try again.")
            elif error:
                print(f"Login failed: {error.details()}")
            else:
                print("Failed to connect to any server.")
            time.sleep(2)

    def validate_token(self):
        if not self.token:
            print("You are not logged in.")
            return False
        request = login_pb2.ValidateTokenRequest(token=self.token)
        response, error = self.send_request('ValidateToken', request)
        if response:
            return True
        elif error:
            if error.code() == grpc.StatusCode.UNAUTHENTICATED:
                print("Session expired or invalid token. Please log in again.")
                self.token = None
            elif error.code() == grpc.StatusCode.UNAVAILABLE:
                print("Server is unavailable. Please try again later.")
            else:
                print(f"An error occurred: {error.details()}")
            return False
        else:
            print("An unexpected error occurred. Please try again.")
            return False

    def view_ungraded_assignments(self):
        if self.validate_token():
            request = login_pb2.ViewUngradedAssignmentsRequest(token=self.token)
            response, error = self.send_request('ViewUngradedAssignments', request)

            if response and response.assignments:
                print("Ungraded Assignments:")
                for i, assignment in enumerate(response.assignments, 1):
                    print(f"{i}. Assignment ID: {assignment.assignment_id}, Student ID: {assignment.student_id}")

                choice = input("Enter the number of the assignment to grade: ")
                if choice.isdigit():
                    choice = int(choice) - 1
                    if 0 <= choice < len(response.assignments):
                        selected_assignment = response.assignments[choice]

                        # Download the assignment
                        self.download_assignment(selected_assignment.assignment_id, selected_assignment.file_path)
                        self.grade_assignment(selected_assignment.assignment_id,selected_assignment.student_id)
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input. Please enter a number.")
            elif response:
                print("No ungraded assignments available.")
            elif error:
                print(f"Error viewing ungraded assignments: {error.details()}")
            else:
                print("An unexpected error occurred while viewing ungraded assignments.")
        else:
            self.login()

    def download_assignment(self, assignment_id, file_path):
        print(f"Downloading assignment {assignment_id} from {file_path}...")
        # Implement actual file download logic if necessary
        print(f"Assignment {assignment_id} downloaded successfully.")

    def grade_assignment(self, assignment_id,student_id):
        grade = input("Enter grade for the assignment: ")
        feedback = input("Enter feedback for the assignment: ")

        request = login_pb2.GradeAssignmentRequest(
            token=self.token,
            assignment_id=assignment_id,
            grade=grade,
            feedback=feedback,
            student_id=student_id
        )
        response, error = self.send_request('GradeAssignment', request)
        if response:
            print(response.message)
        elif error:
            print(f"Error grading assignment: {error.details()}")
        else:
            print("An unexpected error occurred while grading the assignment.")

    def upload_course_material(self):
        if self.validate_token():
            Tk().withdraw()
            file_path = askopenfilename(title="Select Course Material File")
            if file_path:
                with open(file_path, 'rb') as f:
                    data = f.read()
                title = input("Enter the title of the course material: ")
                request = login_pb2.CourseMaterialUploadRequest(token=self.token, title=title, material_data=data)
                response, error = self.send_request('UploadCourseMaterial', request)
                if response:
                    print(response.message)
                elif error:
                    print(f"Error uploading course material: {error.details()}")
                else:
                    print("An unexpected error occurred while uploading course material.")
            else:
                print("No file selected.")
        else:
            self.login()

    def view_queries(self):
        if self.validate_token():
            request = login_pb2.QueryViewRequest(token=self.token)
            response, error = self.send_request('ViewQueries', request)

            if response and response.queries:
                print("Unanswered Queries:")
                for i, query in enumerate(response.queries, 1):
                    print(f"{i}. Query ID: {query.query_id}, Student ID: {query.student_id}, Title: {query.title}, Body: {query.body}")

                choice = input("Enter the number of the query to reply to: ")
                if choice.isdigit():
                    choice = int(choice) - 1
                    if 0 <= choice < len(response.queries):
                        selected_query = response.queries[choice]
                        self.reply_to_query(selected_query.query_id,selected_query.student_id)
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input. Please enter a number.")
            elif response:
                print("No unanswered queries available.")
            elif error:
                print(f"Error viewing queries: {error.details()}")
            else:
                print("An unexpected error occurred while viewing queries.")
        else:
            self.login()

    def reply_to_query(self, query_id,student_id):
        reply = input("Enter your reply to the query: ")

        request = login_pb2.ReplyToQueryRequest(
            token=self.token,
            query_id=query_id,
            student_id=student_id,
            reply=reply
        )
        response, error = self.send_request('ReplyToQuery', request)
        if response:
            print(response.message)
        elif error:
            print(f"Error replying to query: {error.details()}")
        else:
            print("An unexpected error occurred while replying to query.")

    def menu(self):
        while True:
            if not self.validate_token():
                print("Session expired or invalid. Logging in again...")
                if not self.login():
                    break
                continue

            print("\n--- Instructor Menu ---")
            print("1. View Ungraded Assignments")
            print("2. View and Respond to Queries")
            print("3. Upload Course Materials")
            print("0. Logout")
            choice = input("Enter your choice: ")
            if choice == '1':
                self.view_ungraded_assignments()
            elif choice == '2':
                self.view_queries()
            elif choice == '3':
                self.upload_course_material()
            elif choice == '0':
                print("Logging out...")
                self.token = None
                break
            else:
                print("Invalid choice.")

    def find_new_leader(self):
        """Rotate through the list of servers to find a new leader."""
        retries = 0
        max_retries = len(self.server_addresses)
        while retries < max_retries:
            self.current_server_index = (self.current_server_index + 1) % len(self.server_addresses)
            server_address = self.server_addresses[self.current_server_index]
            print(f"Trying server {server_address} to find the leader...")
            try:
                with grpc.insecure_channel(server_address) as channel:
                    stub = login_pb2_grpc.LMSStub(channel)
                    request = login_pb2.ValidateTokenRequest(token=self.token)
                    stub.ValidateToken(request, timeout=2)
                    self.leader_address = server_address
                    print(f"New leader found at {self.leader_address}")
                    return True
            except grpc.RpcError as e:
                print(f"Server {server_address} is not the leader or unavailable.")
                retries += 1
        print("Unable to find a new leader.")
        return False

if __name__ == "__main__":
    # List of server addresses (adjust ports as per your setup)
    if len(sys.argv) < 2:
        print("Usage: python instructor_client.py <server_address1> <server_address2> ...")
        sys.exit(1)

    server_addresses = sys.argv[1:]
    client = InstructorClient(server_addresses)
    if client.login():
        client.menu()