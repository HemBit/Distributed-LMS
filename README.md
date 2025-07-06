# Distributed-LMS

The project consists of Python scripts: `instructorClient.py`, `server.py`, `login.proto`, `tutoringServer.py` and `studentClient.py`. Here’s a summary of their functionality:

   1. **instructorClient \.py**: This file manages instructor operations such as viewing ungraded assignments, grading assignments, and providing feedback. It uses a gRPC connection to communicate with a server and a MySQL database for handling assignment data. <br>
    2.  **server \.py**: This is the server-side implementation, providing gRPC services to handle requests from both the student and instructor clients. It also implements RAFT consesus to ensure fault tolerance and consistency. It interacts with a database to store and retrieve assignments, grades, feedback, etc.<br>
    3.  **studentClient \.py**: This script handles student operations such as uploading assignments, posting queries, checking feedback, and interacting with course materials. It also communicates with the server via gRPC.<br>
    4. **login \.proto**: This is used to define the structure of the data that is exchanged between services and the service’s API.<br> 
    5. **tutoringServer \.py**: This file implements the LLM server which connects the client to a trained LLM via an API call. It provides the user with LLM query solving functionality incase the user opts for it.
### Requirements:

-   Python 3.x (Python 3.7 or higher)
-   gRPC
-   MySQL Connector for Python
-   openai version 0.28
-   Any other dependencies in your code

## Project Overview

This project is a client-server based application with RAFT consensus implementation for student-instructor interactions such as submitting assignments, asking queries, grading, and viewing feedback. It consists of the following components:

-   **Server**: A gRPC server that handles requests from both instructor and student clients and implements RAFT for fault tolerance and consistency.
-   **Instructor Client**: Allows instructors to log in, grade assignments, and provide feedback.
-   **Student Client**: Allows students to log in, upload assignments, ask queries and view grades and feedback.
-   **Tutoring Server**: An LLM server that connects client to an LLM to service query asking functionality for the student client.

## Features

-   Student can upload assignments and view grades.
-   Student can ask queries to either the instructor or an LLM.
-   Instructor can grade assignments and provide feedback.
-   Both clients use gRPC to communicate with the server.
-   Servers can run in any number of systems and if the leader server in unavailable, then one of the followers become leader with updated logs to ensure fault tolerance and cinsistency.
