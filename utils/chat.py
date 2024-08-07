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


async def chat(prompt, content, model=GEMINI_MODEL):
    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": content
        }
    ]

    try:
        response = await CLIENT.chat.completions.create(
            model=model,
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


async def main():
    prompt = """你是一只猫猫，你会用猫猫的语言来回答我的问题。比如"喵喵喵～(翻译：我是一直猫猫！)"。"""
    content = "你喜欢吃什么"
    model = GEMINI_MODEL
    response = await chat(prompt, content, model)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
