import openai

openai.api_key = "your-key"

def generate_sql(question: str, schema: str) -> str:
    with open("app/prompts/base_prompt.txt", "r") as f:
        base_prompt = f.read()

    prompt = f"{base_prompt}\nPergunta: {question}\nSchema: {schema}\nSQL:"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()
