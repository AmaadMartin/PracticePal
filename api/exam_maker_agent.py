import os
from openai import OpenAI
import json

os.environ["OPENAI_API_KEY"] = ""

prompt_instructions = """
Make a practice exam based on the class materials provided. Try to search as many files as possible for relevant information. To make the exam first make a name for the exam using the createExamName function. Then, for each question in the exam use the createQuestion function. The createQuestion function takes in the following parameters:
- question: the actual question to be asked
- type: the type of question to be asked (mc or oe) ONLY mc for multiple choice and oe for open ended are supported
- answer_choices: the answer choices to be provided if the question is multiple choice
- correct_answer: the correct answer to the question
- answer_explanation: an explanation of why the correct answer is correct

Example usage:
createQuestion({
    "question": "What is the capital of France?",
    "type": "mc",
    "answer_choices": ["Paris", "London", "Berlin", "Madrid"],
    "correct_answer": "Paris",
    "answer_explanation": "Paris is the capital of France."
})

Use this function to create a practice exam based on the class materials provided. Make around 10-15 questions for the exam. Make sure to have variety in the question types.
"""

model = "gpt-4o"

class Agent:
    def __init__(self):
        self.client = OpenAI()
        self.file_ids = []
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
        self.data = {}

    def create_conversation(self):
        messages = [
            {
                "role": "user",
                "content": "Can you make a practice exam based on these class materials? Try to search as many files as possible for relevant information.",
                "attachments": [{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in self.file_ids],
            }
        ]
        thread = self.client.beta.threads.create(messages=messages)
        self.data[thread.id] = {"questions": [], "answers": []}
        return thread.id

    def run_agent(self, query, threadId):
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
                                    self.data[threadId]["questions"].append({
                                        "question": args["question"],
                                        "type": args["type"],
                                        "answer_choices": args["answer_choices"]
                                    })
                                elif args["type"] == "oe":
                                    self.data[threadId]["questions"].append({
                                        "question": args["question"],
                                        "type": args["type"]
                                    })

                                self.data[threadId]["answers"].append((args["correct_answer"], args["answer_explanation"]))

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
                                self.data[threadId]["exam_name"] = args["exam_name"]
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

        return messages

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
        for file in files:
            file = self.client.files.create(file=file, purpose="assistants")
            self.file_ids.append(file.id)


def generate_exam_html(questions, output_filename='exam.html'):
    """
    Generates an HTML file to visualize a practice exam based on the list of questions provided.

    :param questions: List of dictionaries containing question data.
    :param output_filename: The name of the output HTML file.
    """
    # HTML template parts
    html_head = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Practice Exam</title>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .question-container {
            margin-bottom: 20px;
        }
        .question-text {
            font-weight: bold;
        }
    </style>
</head>
<body>
<h1>Practice Exam</h1>
<div id="exam-container">
'''

    html_tail = '''
</div>
</body>
</html>'''

    # Generate the body content
    body_content = ''
    for index, q in enumerate(questions):
        question_html = '<div class="question-container">\n'
        # Question text
        question_text = f'<p class="question-text">{index + 1}. {q["question"]}</p>\n'
        question_html += question_text

        if q['type'] == 'mc':
            # Multiple-choice options
            for choice in q['answer_choices']:
                choice_id = f"question-{index}-choice-{q['answer_choices'].index(choice)}"
                choice_html = f'''
<label>
    <input type="radio" name="question-{index}" value="{choice}">
    {choice}
</label><br>
'''
                question_html += choice_html
        elif q['type'] == 'oe':
            # Open-ended question
            textarea_html = f'''
<textarea name="question-{index}" rows="4" cols="50"></textarea>
'''
            question_html += textarea_html
        else:
            # Unsupported question type
            error_html = '<p style="color: red;">Unsupported question type.</p>\n'
            question_html += error_html

        question_html += '</div>\n'
        body_content += question_html

    # Combine all parts and write to the output file
    full_html = html_head + body_content + html_tail

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"Exam HTML file has been generated: {output_filename}")

