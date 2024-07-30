import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("KEY")
URL = os.getenv("URL")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GPT4O_MODEL = os.getenv("GPT4O_MODEL")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL")

CLIENT = AsyncOpenAI(api_key=KEY, base_url=URL)

SYSTEM_PROMPT = """
I will provide you with content from several admissions web pages. Your task is to carefully read all the content and then extract key information according to the specified JSON format below:

{
  "selection_process_and_criteria": {
    "selection_process": {},
    "selection_criteria": {}
  },
  "admission_requirements": {
    "university_level": {
      "overview": "",
      "GPA_requirement": {
        "guidelines": "",
        "general_requirement": "",
        "minimum_required_GPA": -1,
        "relevant_links": []
      },
      "English_proficiency_requirements": [{
        "test_name": "",
        "guidelines": "",
        "is_required": "",
        "general_requirement": "",
        "minimum_required_score": -1,
        "breakdown_requirements": "",
        "accepted_test_type": "",
        "waive_conditions": "",
        "relevant_links": []
      }],
      "application_fee": {
        "overview": "",
        "value": ""
      },
      "application_materials": [{
        "material_name": "",
        "guidelines": "",
        "detailed_requirement": ""
      }],
      "prerequisite_courses": [],
      "other_requirements": []
    },
    "school_college_level": {}
  },
  "application_deadlines": {
    "early_application": {
      "intro": "",
      "actions_after_admission": ""
    },
    "deadlines_by_type": [],
    "relevant_links": []
  }
}

Guidelines:
- Distinguish between general requirements and international student requirements where applicable. Separate entries into two distinct keys in the JSON structure.
- Some institutions may have specific requirements at the school or college level; organize these accordingly.
- Integrate data from different links to avoid redundancy.
- Exclude requirements specific to non-traditional, home-schooled, military, disabled, DACA, resumed education, QuestBridge, GED, or returning students.
- Focus solely on requirements for freshmen or first-year applicants, excluding transfer students and pathway programs.

Please ensure all information is consolidated effectively and accurately into the provided JSON structure.
"""


async def generate_response(content):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": content
        }
    ]

    try:
        response = await CLIENT.chat.completions.create(
            model=GPT4O_MODEL,
            messages=messages,
            temperature=0.6,
            stream=True
        )
        final = ''
        async for chunk in response:
            # print("Streamed chunk:", chunk)
            if chunk.choices:
                if chunk.choices[0].delta:
                    if chunk.choices[0].delta.content is not None:
                        final += chunk.choices[0].delta.content

        # print(final)
        return final
    except Exception as e:
        print(f"An error occurred: {type(e).__name__}, {str(e)}")
        return None


def read_markdown_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            content = content.replace('\n', '')
        return content
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None


async def get_response():
    content = read_markdown_file("src/harvard.md")
    response = await generate_response(content)
    return response


async def main():
    response = await get_response()
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
