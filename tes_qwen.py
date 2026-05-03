from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()  # loads .env from current working directory

try:
    client = OpenAI(
        # The API keys for the Singapore/US and China (Beijing) regions are different. To get an API key, see https://www.alibabacloud.com/help/en/model-studio/get-api-key
        # If the environment variable is not set, replace the following line with your Model Studio API key: api_key = "sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        # The following URL is for the Singapore/US region. If you use a model in the China (Beijing) region, replace the URL with: https://dashscope.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )
    
    prompt = """
        You are FARIS, an English academic speaking evaluator for university students.

        Your task:
        1. Transcribe the student's speech accurately.
        2. Evaluate the speaking performance based on:
           - Fluency
           - Grammar
           - Pronunciation
           - Vocabulary

        Give score from 1 to 4 for each aspect.
        Provide short feedback and suggestions for improvement.
        Use clear and simple English.
        """

    stream_enabled = False  # Whether to enable streaming output
    completion = client.chat.completions.create(
        model="qwen3-asr-flash",
        messages=[
            {
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"
                        }
                    }
                ],
                "role": "user"
            }
        ],
        stream=stream_enabled,
        # When stream is set to False, you cannot set the stream_options parameter.
        # stream_options={"include_usage": True},
        extra_body={
            "asr_options": {
                # "language": "zh",
                "enable_itn": False
            }
        }
    )
    if stream_enabled:
        full_content = ""
        print("Streaming output content:")
        for chunk in completion:
            # If stream_options.include_usage is True, the choices field of the last chunk is an empty list and should be skipped. You can get the token usage from chunk.usage.
            print(chunk)
            if chunk.choices and chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content
        print(f"Full content: {full_content}")
    else:
        print(f"Non-streaming output content: {completion.choices[0].message.content}")
except Exception as e:
    print(f"Error message: {e}")