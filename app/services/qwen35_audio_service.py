# app/services/qwen35_audio_service.py

import os
import base64
import mimetypes
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import FARIS_PROMPT


load_dotenv()


class Qwen35AudioService:
    def __init__(self):
        self.model_name = os.getenv("QWEN_MODEL_NAME", "qwen3.5-omni-flash")

        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is not set in .env")

        print("Initializing Qwen3.5 Omni Flash client...")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        print("Qwen3.5 Omni Flash client initialized successfully.")

    def _guess_audio_format(self, audio_path_or_url: str) -> str:
        """
        Guess audio format from file extension.
        Qwen Omni usually accepts common formats such as mp3, wav, m4a, webm, etc.
        """
        ext = os.path.splitext(audio_path_or_url.split("?")[0])[1].lower()

        mapping = {
            ".mp3": "mp3",
            ".wav": "wav",
            ".m4a": "m4a",
            ".ogg": "ogg",
            ".webm": "webm",
            ".flac": "flac",
        }

        return mapping.get(ext, "mp3")

    def _encode_local_audio(self, audio_path: str) -> str:
        """
        Convert local audio file to base64 string.
        Used when audio_url is not provided.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        return base64.b64encode(audio_bytes).decode("utf-8")

    def evaluate_audio(
        self,
        audio_path: Optional[str] = None,
        audio_url: Optional[str] = None,
        max_new_tokens: int = 1800,
        prompt: Optional[str] = None,
        print_stream: bool = False,
    ) -> str:
        """
        Evaluate student's speaking audio using Qwen3.5 Omni Flash.

        Parameters:
        - audio_path: local audio file path
        - audio_url: public audio URL
        - max_new_tokens: maximum generated text tokens
        - prompt: custom prompt, default uses FARIS_PROMPT
        - print_stream: if True, print generated text while streaming

        Returns:
        - response text from Qwen3.5 Omni Flash
        """

        if not audio_path and not audio_url:
            raise ValueError("Either audio_path or audio_url must be provided.")

        final_prompt = prompt or FARIS_PROMPT

        audio_source = audio_url or audio_path
        audio_format = self._guess_audio_format(audio_source)

        if audio_url:
            audio_data = audio_url
        else:
            audio_data = self._encode_local_audio(audio_path)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_data,
                            "format": audio_format,
                        },
                    },
                    {
                        "type": "text",
                        "text": final_prompt,
                    },
                ],
            }
        ]

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,

            # FARIS hanya butuh output text
            modalities=["text"],

            # Untuk Qwen Omni, stream=True diperlukan
            stream=True,
            stream_options={"include_usage": True},

            # Mirip max_new_tokens pada HF
            max_tokens=max_new_tokens,

            # Deterministic evaluation
            temperature=0,
        )

        full_text = ""
        usage = None

        for chunk in completion:
            if chunk.choices:
                delta = chunk.choices[0].delta

                if delta.content:
                    full_text += delta.content

                    if print_stream:
                        print(delta.content, end="", flush=True)
            else:
                usage = chunk.usage

        if print_stream:
            print("\n")

        return full_text.strip()