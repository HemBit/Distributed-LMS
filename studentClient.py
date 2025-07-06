import grpc
import warnings
import login_pb2
import login_pb2_grpc
import sys
import os
import time
import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename
os.environ['TK_SILENCE_DEPRECATION'] = '1'
warnings.filterwarnings("ignore", message="Protobuf gencode version.*")

class StudentClient:
    def __init__(self, server_addresses):
        self.server_addresses = server_addresses  # List of server addresses
        self.current_server_index = 0
        self.leader_address = self.server_addresses[0]
        self.token = None
        self.assignment_uploaded = False  # Track if an assignment is uploaded

    # def get_channel(self):
    #     server_address = self.server_addresses[self.current_server_index]
    #     return grpc.insecure_channel(server_address)

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
                    if response.user_type == "student":
                        print(f"Login successful! Token: {response.token}")
                        self.token = response.token
                        return True
                    else:
                        print("Error: This login is only for students.")
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

    def check_assignment_status(self):
        if self.validate_token():
            request = login_pb2.AssignmentStatusRequest(token=self.token)
            response, error = self.send_request('CheckAssignmentStatus', request)
            if response:
                self.assignment_uploaded = response.uploaded
                return self.assignment_uploaded
            elif error:
                print(f"Error checking assignment status: {error.details()}")
                return False
            else:
                print("An unexpected error occurred while checking assignment status.")
                return False
        else:
            self.login()
            return False

    def upload_assignment(self):
        if self.validate_token():
            Tk().withdraw()
            file_path = askopenfilename(title="Select Assignment File")
            if file_path:
                with open(file_path, 'rb') as f:
                    data = f.read()
                request = login_pb2.AssignmentUploadRequest(token=self.token, assignment_data=data)
                response, error = self.send_request('UploadAssignment', request)
                if response:
                    print(response.message)
                    self.assignment_uploaded = True
                elif error:
                    print(f"Error uploading assignment: {error.details()}")
                else:
                    print("An unexpected error occurred while uploading assignment.")
            else:
                print("No file selected.")
        else:
            self.login()

    def check_feedback_and_grade(self):
        if self.validate_token():
            request = login_pb2.FeedbackRequest(token=self.token)
            response, error = self.send_request('CheckFeedback', request)
            if response:
                if response.graded:
                    print(f"Grade: {response.grade}")
                else:
                    print("Assignment not graded yet.")
                if response.feedback:
                    print(f"Feedback: {response.feedback}")
                else:
                    print("No feedback provided yet.")
            elif error:
                print(f"Error checking feedback and grade: {error.details()}")
            else:
                print("An unexpected error occurred while checking feedback and grade.")
        else:
            self.login()

    def post_query(self):
        if self.validate_token():
            query_title = input("Enter the subject of your query: ")
            query_body = input("Enter your query for the instructor: ")
            print("Select who should reply to the query:")
            print("1. Instructor")
            print("2. LLM")
            query_type = input("Enter your choice: ")
            if query_type == '1':
                request = login_pb2.QueryRequest(token=self.token, title=query_title, query=query_body)
                response, error = self.send_request('PostQuery', request)
                if response:
                    print(response.message)
                elif error:
                    print(f"Error posting query: {error.details()}")
                else:
                    print("An unexpected error occurred while posting query.")
            elif query_type == '2':
                request = login_pb2.QuestionRequest(token=self.token, question=query_body)
                response, error = self.send_request('AskQuestion', request)
                if response:
                    print(f"Received answer: {response.answer}")
                elif error:
                    print(f"Error getting answer from LLM: {error.details()}")
                else:
                    print("An unexpected error occurred while getting answer from LLM.")
            else:
                print("Invalid choice.")
        else:
            self.login()

    def check_query_reply(self):
        if self.validate_token():
            request = login_pb2.CheckQueryReplyRequest(token=self.token)
            response, error = self.send_request('CheckQueryReply', request)
            if response:
                if response.reply:
                    print(f"Query Reply: {response.reply}")
                else:
                    print("Query not replied yet.")
            elif error:
                print(f"Error checking query reply: {error.details()}")
            else:
                print("An unexpected error occurred while checking query reply.")
        else:
            self.login()

    def view_course_materials(self):
        if self.validate_token():
            request = login_pb2.CourseMaterialListRequest(token=self.token)
            response, error = self.send_request('ListCourseMaterials', request)
            if response and response.titles:
                print("Available Course Materials:")
                for i, title in enumerate(response.titles, start=1):
                    print(f"{i}. {title}")
                choice = input("Enter the number of the material to download: ")
                if choice.isdigit():
                    choice = int(choice)
                    if 1 <= choice <= len(response.titles):
                        self.download_course_material(response.titles[choice - 1])
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input. Please enter a number.")
            elif response:
                print("No course materials available.")
            elif error:
                print(f"Error retrieving course materials: {error.details()}")
            else:
                print("An unexpected error occurred while retrieving course materials.")
        else:
            self.login()

    def download_course_material(self, title):
        if self.validate_token():
            request = login_pb2.CourseMaterialDownloadRequest(token=self.token, title=title)
            response, error = self.send_request('DownloadCourseMaterial', request)
            if response and response.content:
                with open(f"{title}.pdf", 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded '{title}' successfully.")
            elif response:
                print(response.message)
            elif error:
                print(f"Error downloading course material: {error.details()}")
            else:
                print("An unexpected error occurred while downloading course material.")
        else:
            self.login()

    def menu(self):
        while True:
            if not self.validate_token():
                print("Session expired or invalid. Logging in again...")
                if not self.login():
                    break
                continue

            print("\n--- Student Menu ---")
            if not self.assignment_uploaded:
                self.check_assignment_status()

            if not self.assignment_uploaded:
                print("1. Upload Assignment")
                print("2. Post Query")
                print("3. Check Query Reply")
                print("4. View Course Materials")
            else:
                print("1. Check Feedback and Grade")
                print("2. Post Query")
                print("3. Check Query Reply")
                print("4. View Course Materials")
            print("0. Logout")

            choice = input("Enter your choice: ")

            if choice == '1' and not self.assignment_uploaded:
                self.upload_assignment()
            elif choice == '1' and self.assignment_uploaded:
                self.check_feedback_and_grade()
            elif choice == '2':
                self.post_query()
            elif choice == '3':
                self.check_query_reply()
            elif choice == '4':
                self.view_course_materials()
            elif choice == '0':
                print("Logging out...")
                self.token = None
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    # List of server addresses (adjust ports as per your setup)
    if len(sys.argv) < 2:
        print("Usage: python student_client.py <server_address1> <server_address2> ...")
        sys.exit(1)

    server_addresses = sys.argv[1:]
    client = StudentClient(server_addresses)
    if client.login():
        client.menu()