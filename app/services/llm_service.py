import os
import openai
from app.models.query_request import QueryRequest

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "base_prompt.txt")
with open(PROMPT_PATH, "r") as f:
    BASE_PROMPT = f.read()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_query(request: QueryRequest) -> str:
    prompt = BASE_PROMPT.format(user_input=request.user_input, table_schema=request.table_schema)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response['choices'][0]['message']['content'].strip()
