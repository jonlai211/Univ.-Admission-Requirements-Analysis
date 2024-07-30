import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key='sk-ElSpFcfMJtlVRfiWA627F572C071404fB22287358c89B938',
                base_url='https://vip-api-aiearth-hk.zeabur.app/v1')

messages = [
    {
        "role": "system",
        "content": """你是一个说中文的AI助手"""
    },
    {
        "role": "user",
        "content": """帮我写个关于哈利波特的短篇小说"""
    }
]

response = client.chat.completions.create(
    model='claude-3-5-sonnet-20240620', messages=messages, stream=True)

length = 0

output = ""

for chunk in response:
    if chunk.choices != []:
        output += chunk.choices[0].delta.content

print(output)
