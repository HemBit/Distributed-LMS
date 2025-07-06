import grpc
import openai  # For OpenAI API calls
from concurrent import futures
import login_pb2
import login_pb2_grpc

openai.api_key = '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'  # Replace with your actual API key


class LMSService(login_pb2_grpc.LMSServicer):
    def __init__(self):
        self.context_string = (
            "You are an assistant specializing in Advanced Operating Systems. "
            "You provide brief answers under 300 characters on topics such as distributed systems, "
            "distributed mutual exclusion algorithms, time synchronization in distributed systems, "
            "agreement protocols like Byzantine agreement and Raft, leader election algorithms, "
            "distributed deadlock detection, distributed file systems (including HDFS and MapReduce), "
            "and fault tolerance in distributed transactions. You also assist with recent research areas "
            "like blockchain and consensus algorithms. Maximum characters=300"
        )
    def GenerateAnswer(self, request, context):
        question = request.question
        print(f"Received query: {question}")
        
        # Generate answer using ChatGPT-4 with the given context and 50 tokens limit
        answer = self.get_chatgpt_answer(question)
        return login_pb2.AnswerResponse(answer=answer)

    def get_chatgpt_answer(self, question):
        # Combine context and question
        full_prompt = f"{self.context_string}\n\nUser query: {question}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.context_string},
                    {"role": "user", "content": question}
                ],
                max_tokens=80,  # Limit output to 50 tokens
                temperature=0.7  # Adjust the temperature for more or less randomness
            )
            # Extract the response from GPT-4
            return response['choices'][0]['message']['content'].strip()

        except Exception as e:
            print(f"Error while fetching response: {e}")
            return "Sorry, there was an error generating the response."


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    login_pb2_grpc.add_LMSServicer_to_server(LMSService(), server)
    server.add_insecure_port(server_address)    
    server.start()
    print(f"LLM Answer Generation Server started on {server_address}.")
    server.wait_for_termination()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tutoring_server.py <server_address>")
        print("Example: python tutoring_server.py 192.168.1.100:50010")
        sys.exit(1)

    server_address = sys.argv[1]
    serve(server_address)
