from openai import OpenAI
from pydantic import BaseModel
from typing import List
import os
import json
import SearchQueryAgent

# Initialize OpenAI client
openai_client = OpenAI()
openai_client.api_key = os.getenv("OPENAI_API_KEY")

class SearchQueryResponseFormat(BaseModel):
    search_queries: List[str]

class RelevantFilesResponseFormat(BaseModel):
    relevant_files: List[int]

search_query_agent = SearchQueryAgent.Agent()

# Generate multiple search queries using GPT-4o-mini
prompt = """
Generate 5 different search queries to find lecture notes, PDFs, or slides for a course or relevant courses with the following details:

Class Name: {class_name}
School: {school}
Topics: {topics}

Focus on finding educational materials relevant to the course, such as 'lecture notes', 'course slides', 'syllabus', etc. Include keywords that are likely to yield downloadable files. Search up each topic individually to find relevant materials for each topic.

Return the search queries as a JSON array of strings.
"""

second_prompt = """
Given this list of files returned from these search queries to find lecture notes, PDFs, or slides for a course or relevant courses:

Filenames: {files}
Search queries: {search_queries}

Remove any irrelevant files (Schedules, Syllabus, Different subject, Different school etc.) from the list and sort it from most relevant to least relevant indices as a JSON array of integers. Make sure all of the files kept are RELEVANT.
** IF THE FILE IS NOT OBVIOUSLY RELEVANT REMOVE IT **
"""

def generate_search_queries(files, class_name, school, topics):
    threadId = search_query_agent.create_conversation(files, class_name, school, topics)
    data = search_query_agent.run_agent(threadId)
    search_queries = data["search_queries"]
    print("generate_search_queries", search_queries)
    return search_queries


def filter_file_names(files, search_queries):
    response = openai_client.beta.chat.completions.parse(
        messages=[{"role": "user", "content": second_prompt.format(files=files, search_queries=search_queries)}],
        model="gpt-4o-mini",
        max_tokens=200,
        temperature=0.7,
        response_format=RelevantFilesResponseFormat
    )

    # Extract the indices of relevant files
    relevant_files = response.choices[0].message.parsed.relevant_files

    return relevant_files