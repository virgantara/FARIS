import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.prompts import FARIS_PROMPT

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

audio_url = "https://easpod-storage.unidagontor.ac.id/audio/assigment/1778306522_69fecdda509b5.webm"


completion = client.chat.completions.create(
    model="qwen3.5-omni-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_url,
                        "format": "mp3",
                    },
                },
                {
                    "type": "text",
                    "text": FARIS_PROMPT,
                },
            ],
        }
    ],

    # For FARIS evaluation, use text output only.
    modalities=["text"],

    # stream=True is required for Qwen-Omni
    stream=True,
    stream_options={"include_usage": True},
)

full_text = ""
usage = None

for chunk in completion:
    if chunk.choices:
        delta = chunk.choices[0].delta

        if delta.content:
            full_text += delta.content
            print(delta.content, end="", flush=True)
    else:
        usage = chunk.usage

print("\n\nUsage:")
print(usage)