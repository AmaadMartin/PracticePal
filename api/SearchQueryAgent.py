# exam_maker_agent.py

import os
from openai import OpenAI
import json
from dotenv import load_dotenv
from Prompt import search_prompt_instructions

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

QUERY_PROMPT = """
Generate 5 different search queries to find lecture notes, PDFs, or slides for a course or relevant courses with the following details:

Class Name: {class_name}
School: {school}
Topics: {topics}

Focus on finding educational materials relevant to the course, such as 'lecture notes', 'course slides', 'syllabus', etc. Include keywords that are likely to yield downloadable files. Search up each topic individually to find relevant materials for each topic.

Return the search queries as a JSON array of strings.
"""

model = "gpt-4o-mini"

class Agent:
    def __init__(self):
        self.client = OpenAI()
        self.agent = self.client.beta.assistants.create(
            name="Class Material Search Agent",
            instructions=search_prompt_instructions,
            tools=[
                {"type": "code_interpreter"},
                {
                    "type": "function",
                    "function": {
                        "name": "AddSearchQuery",
                        "description": "Adds a search query to the list of search queries",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "search_query": {
                                    "type": "string",
                                    "description": "the search query to be added"
                                }
                            },
                            "required": ["search_query"]
                        }
                    }
                },
                {"type": "file_search"}
            ],
            model=model,
            temperature=1.2
        )

    def create_conversation(self, files, class_name, school, topics):
        # print(files) 
        file_ids = self.add_files(files)
        messages = [
            {
                "role": "user",
                "content": QUERY_PROMPT.format(class_name=class_name, school=school, topics=topics),
                "attachments": [{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in file_ids],
            }
        ]
        thread = self.client.beta.threads.create(messages=messages)
        return thread.id

    def run_agent(self, threadId):
        data = {
            "search_queries": []
        }

        # create run for assistant
        run = self.client.beta.threads.runs.create(
            thread_id=threadId,
            assistant_id=self.agent.id
        )

        # retrieve status of run
        while run.status in ["queued", "in_progress", "requires_action"]:
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
                        if toolCall.function.name == "AddSearchQuery":
                            if toolCall.function.arguments:
                                args = json.loads(toolCall.function.arguments)
                                print("agent args", args)

                                data["search_queries"].append(args["search_query"]) 
                                print("agent data", data)
                                

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
        print(data)

        return data

    def delete_thread(self, threadId):
        self.client.beta.threads.delete(threadId) 

    def add_files(self, files):
        file_ids = []
        for file in files:
            # print(filename)
            # print(file_obj)
            file_response = self.client.files.create(file=file, purpose="assistants")
            file_ids.append(file_response.id)
        return file_ids