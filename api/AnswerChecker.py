import os
from openai import OpenAI
from dotenv import load_dotenv
import json
load_dotenv()


os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def isCorrectOpenEndedAnswer(answer, correct_answer, explanation):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that determines if a student's answer is correct based on the reference answer and explanation provided. If the answer is blank or incorrect, you should return False. If the answer is correct, you should return True. Provide a short reason for your decision. Don't overly rely on the reference answer. For example, if the answer requires an example consider if it works for the answer even if it's different." 
            ),
        },
        {
            "role": "user",
            "content": f"Student Answer: {answer}\n\rReference Answer: {correct_answer}\n\nExplanation: {explanation}",
        },
    ]

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "math_response",
            "schema": {
                "type": "object",
                "properties": {
                    "short_reason": {"type": "string"},
                    "correct": {"type": "string"}
                },
                "required": ["short_reason", "correct"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
    )
    json_response = json.loads(response.choices[0].message.content)
    print(json_response)
    isCorrect = bool(json_response["correct"])
    return isCorrect

if __name__ == "__main__":
    answer = "Paris"
    correct_answer = "Paris"
    explanation = "Paris is the capital of France."
    print(isCorrectOpenEndedAnswer(answer, correct_answer, explanation))
