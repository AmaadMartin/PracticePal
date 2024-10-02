from fastapi import FastAPI, UploadFile, File
import uvicorn
from exam_maker_agent import Agent
import tempfile
import shutil
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()

test_questions = [
    {
        "question": "What is the capital of France?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Paris"
    },
    {
        "question": "What is the capital of Germany?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Berlin"
    },
    {
        "question": "What is the capital of Spain?",
        "type": "mc",
        "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
        "correct_answer": "Madrid"
    },
    {
        "question": "What is the capital of England?",
        "type": "oe",
        "correct_answer": "London"
    }
]

@app.post("/create_exam")
async def create_exam(files: list[UploadFile] = File(...)):
    
    # response = {
    #     "examName": "Test Exam",
    #     "questions": test_questions
    # }
    # return response

    # convert files to list of file objects while keeping their extensions
    files = [(file.filename, file.file) for file in files]
    agent.add_files(files)
    threadId = agent.create_conversation()
    agent.run_agent("Can you make a practice exam based on these class materials? Try to search as many files as possible for relevant information.", threadId)
    
    examName = agent.data[threadId]["exam_name"]
    questions = agent.data[threadId]["questions"]
    answers = agent.data[threadId]["answers"]
    response = {
        "examName": examName,
        "questions": questions,
        "answers": answers
    }
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)