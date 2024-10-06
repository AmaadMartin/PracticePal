import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from Prompt import prompt_instructions
load_dotenv()


os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

QUERY_PROMPT = "Generate a practice exam based on these files."

model = "gpt-4o-mini"

class Agent:
    def __init__(self):
        self.client = OpenAI()
        self.agent = self.client.beta.assistants.create(
            name="Exam Maker",
            instructions=prompt_instructions,
            tools=[{"type": "code_interpreter"}, {
                "type": "function",
                "function": {

                    "name": "createQuestion",
                    "description": "Adds a Question to the exam given the question, the type of question, answer choices, and the correct answer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string",
                                         "description": "the actual question to be asked"},
                            "type": {"type": "string",
                                     "description": "the type of question to be asked (mc or oe) ONLY mc for multiple choice and oe for open ended are supported"},
                            "answer_choices": {"type": "array",
                                                "items": {"type": "string"},
                                               "description": "the answer choices to be provided if the question is multiple choice"},
                            "correct_answer": {"type": "string",
                                               "description": "the correct answer to the question"},
                            "answer_explanation": {"type": "string",
                                                    "description": "an explanation of why the correct answer is correct"}
                        },
                        "required": ["question", "type", "correct_answer"]
                    }
                }
            }, {"type": "function",
                "function": {                   
                    "name": "createExamName",
                    "description": "Creates a name for the exam",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "exam_name": {"type": "string",
                                         "description": "the name of the exam"}
                        },
                        "required": ["exam_name"]
                    }
                }
            }
            ,{"type": "file_search"}],
            model=model
        )

    def create_conversation(self, files):
        file_ids = self.add_files(files)
        messages = [
            {
                "role": "user",
                "content": QUERY_PROMPT,
                "attachments": [{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in file_ids],
            }
        ]
        thread = self.client.beta.threads.create(messages=messages)
        return thread.id

    def run_agent(self, query, threadId):
        data = {
            "exam_name": "",
            "questions": []
        }

        # create run for assistant
        run = self.client.beta.threads.runs.create(
            thread_id=threadId,
            assistant_id=self.agent.id
        )

        # retrieve status of run
        while run.status == "queued" or run.status == "in_progress" or run.status == "requires_action":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=threadId,
                run_id=run.id
            )
            if run.status == "requires_action" and run.required_action.type == "submit_tool_outputs":
                toolCalls = run.required_action.submit_tool_outputs.tool_calls
                toolOutputs = []
                print(toolCalls)

                for toolCall in toolCalls:
                    try:
                        if toolCall.function.name == "createQuestion":
                            if toolCall.function.arguments:
                                args = json.loads(toolCall.function.arguments)
                                print(args)
                                if args["type"] == "mc" :
                                    data["questions"].append({
                                        "question": args["question"],
                                        "type": args["type"],
                                        "answer_choices": args["answer_choices"],
                                        "correct_answer": args["correct_answer"],
                                        "explanation": args["answer_explanation"]
                                    })
                                elif args["type"] == "oe":
                                    data["questions"].append({
                                        "question": args["question"],
                                        "type": args["type"],
                                        "correct_answer": args["correct_answer"],
                                        "explanation": args["answer_explanation"]
                                    })

                                # Do something with args
                                toolOutputs.append({
                                    "tool_call_id": toolCall.id,
                                    "output": "success"
                                })
                            else:
                                toolOutputs.append({
                                    "tool_call_id": toolCall.id,
                                    "output": "no arguments provided"
                                })
                        elif toolCall.function.name == "createExamName":
                            if toolCall.function.arguments:
                                args = json.loads(toolCall.function.arguments)
                                data["exam_name"] = args["exam_name"]
                                toolOutputs.append({
                                    "tool_call_id": toolCall.id,
                                    "output": "success"
                                })
                            else:
                                toolOutputs.append({
                                    "tool_call_id": toolCall.id,
                                    "output": "no arguments provided"
                                })
                    except Exception as e:
                        toolOutputs.append({
                            "tool_call_id": toolCall.id,
                            "output": str(e)
                        })

                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=threadId,
                    run_id=run.id,
                    tool_outputs=toolOutputs
                )

        messages = self.client.beta.threads.messages.list(
            thread_id=threadId,
            order="asc"
        )

        messages = list(map(lambda x: {"role": x.role, "value": x.content[0].text.value}, messages.data))
        print(messages)

        return data

    def delete_thread(self, threadId):
        self.client.beta.threads.delete(threadId) 

    def process_files(self):
        file_ids = []
        for filename in os.listdir("files"):
            with open(f"files/{filename}", "rb") as file:
                file = self.client.files.create(file=file, purpose="assistants")
                file_ids.append(file.id)
        return file_ids

    def add_files(self, files):
        file_ids = []
        for file in files:
            file = self.client.files.create(file=file, purpose="assistants")
            file_ids.append(file.id)
        return file_ids