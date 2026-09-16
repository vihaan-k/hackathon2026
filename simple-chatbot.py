from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat(history: list[dict]):
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=history
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    history = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        history.append({'role': 'user', 'content': user_input})
        response = chat(history)
        print(f"Bot: {response}")
        history.append({'role': 'assistant', 'content': response})