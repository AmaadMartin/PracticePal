from openai import OpenAI
from pydantic import BaseModel
from typing import List
import os
import json

# Initialize OpenAI client
openai_client = OpenAI()
openai_client.api_key = os.getenv("OPENAI_API_KEY")

class SearchQueryResponseFormat(BaseModel):
    search_queries: List[str]

class RelevantFilesResponseFormat(BaseModel):
    relevant_files: List[int]

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

Remove any irrelevant files (Schedules, Syllabus, etc.) from the list and return the indices of the relevant files as a JSON array of integers.
"""

def generate_search_queries(class_name, school, topics):

    # Generate search queries using GPT-4o-mini


    response = openai_client.beta.chat.completions.parse(
        messages=[{"role": "user", "content": prompt.format(class_name=class_name, school=school, topics=topics)}],
        model="gpt-4o-mini",
        max_tokens=200,
        temperature=0.7,
        response_format=SearchQueryResponseFormat
    )

    # Extract the generated search queries
    search_queries = response.choices[0].message.parsed.search_queries

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