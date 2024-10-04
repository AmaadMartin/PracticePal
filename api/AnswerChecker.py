from pydantic import BaseModel
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

class AnswerCheckerResponseFormat(BaseModel):
    short_reason: str
    correct: bool

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
        response_format=AnswerCheckerResponseFormat
    )
    print(response.choices[0].message.parsed.short_reason)
    isCorrect = response.choices[0].message.parsed.correct
    return isCorrect

if __name__ == "__main__":
    answer = "Paris"
    correct_answer = "Paris"
    explanation = "Paris is the capital of France."
    print(isCorrectOpenEndedAnswer(answer, correct_answer, explanation))
