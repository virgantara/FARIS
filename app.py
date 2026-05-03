import os
import tempfile
import requests
import torch
import librosa

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEFAULT_MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "700"))

# =========================
# FastAPI App
# =========================
app = FastAPI(
    title="FARIS Speaking Evaluation API",
    description="Audio URL -> Qwen2-Audio-7B-Instruct -> FARIS speaking evaluation",
    version="1.0.0"
)


# =========================
# Request Schema
# =========================
class AudioUrlRequest(BaseModel):
    audio_url: str
    max_new_tokens: int | None = None


# =========================
# FARIS Prompt
# =========================
FARIS_PROMPT = """
You are FARIS, an English academic speaking evaluator for university students.

Your task is to analyze the student's spoken English from the audio.

First, transcribe the student's speech as accurately as possible.
Then evaluate the student's speaking performance based on these four aspects:

1. Fluency
2. Grammar
3. Pronunciation
4. Vocabulary

Use ONLY the rubrics below. Do not create additional criteria outside the rubric.

==================================================
A. FLUENCY RUBRIC
==================================================

Beginner:
- Frequent pauses and long silence
- Many hesitation markers such as "uh" and "um"
- Speech is slow and not continuous
- Difficulty continuing sentences

Intermediate:
- Some pauses but can continue speaking
- Occasional hesitation
- Speech is fairly smooth
- Can express ideas with some effort

Advanced:
- Smooth and continuous speech
- Minimal pauses or hesitation
- Natural speech rate
- Ideas flow clearly and confidently

Fluency Feedback Bank:

Beginner:
- Your speech has many pauses, so it is not very smooth yet.
- You sometimes stop and have difficulty continuing your speech.
- Try to speak more continuously and reduce long pauses.

Intermediate:
- You speak quite well, but there are some pauses while you think.
- You sometimes stop, but you can continue your speech.

Advanced:
- You speak smoothly and can express your ideas clearly.

==================================================
B. GRAMMAR RUBRIC
==================================================

Beginner:
- Uses simple sentence patterns, mainly Subject-Verb-Object
- Frequent grammar errors
- Limited control of tense, mostly incorrect or inconsistent

Intermediate:
- Uses mostly correct simple sentences
- Some grammar mistakes but meaning is clear
- Basic control of tenses, mainly simple present

Advanced:
- Uses correct and varied sentence structures
- Few or minor errors
- Good control of tenses and subject-verb agreement

Grammar Feedback Bank:

Beginner:
- You make several grammar errors when forming sentences.
- Try to use correct sentence patterns, especially in simple present tense.

Intermediate:
- There are some grammar mistakes, but your meaning is still clear.
- Your sentences are mostly correct with a few small mistakes.

Advanced:
- You can make simple sentences correctly.

==================================================
C. PRONUNCIATION RUBRIC
==================================================

Beginner:
- Many unclear or mispronounced words
- Difficult to understand in some parts
- Weak stress and intonation

Intermediate:
- Mostly understandable
- Some pronunciation errors
- Basic control of stress and intonation

Advanced:
- Clear and easy to understand
- Accurate pronunciation of most words
- Natural stress and intonation

Pronunciation Feedback Bank:

Beginner:
- Your pronunciation makes it difficult to understand some parts.
- Try to practice pronouncing common words more clearly.

Intermediate:
- Some words are not pronounced clearly, but your speech is understandable.
- Most of your words are clear, with a few pronunciation mistakes.

Advanced:
- Your pronunciation is clear and easy to understand.

==================================================
D. VOCABULARY RUBRIC
==================================================

Beginner:
- Uses very basic campus words, such as class, friend, campus, study, homework
- Limited vocabulary range
- Frequent repetition
- Sometimes incorrect word use

Intermediate:
- Uses a wider range of campus-related vocabulary, such as assignment, lecturer, schedule, subject, activity
- Vocabulary is mostly appropriate
- Some variation but still limited
- Occasional lexical errors

Advanced:
- Uses varied and more specific vocabulary, such as presentation, deadline, academic activity, discussion, participate
- Rare repetition
- Accurate and appropriate word choice
- Can express ideas more precisely

Vocabulary Feedback Bank:

Beginner:
- Your vocabulary is limited, so your ideas are not fully expressed.
- You use basic words, but sometimes repeat the same words.
- You sometimes use words that are not suitable for the topic.

Intermediate:
- Your vocabulary is suitable for talking about your daily campus activities.
- You use simple words, but there is still limited variation.

Advanced:
- You use simple and appropriate words related to campus life.

==================================================
EVALUATION INSTRUCTIONS
==================================================

Analyze each aspect independently.

For each aspect:
1. Decide the level: Beginner, Intermediate, or Advanced.
2. Give a short reason based on the student's speech.
3. Select or adapt feedback from the feedback bank.
4. Provide one practical improvement suggestion.

Be fair and supportive.
Use simple English suitable for university students.
Do not be too harsh.
If the audio is unclear, mention that the evaluation may be limited by audio quality.

==================================================
OUTPUT FORMAT
==================================================

Transcript:
...

Overall Speaking Level:
Beginner / Intermediate / Advanced

Summary:
...

1. Fluency
Level:
Beginner / Intermediate / Advanced

Reason:
...

Feedback:
...

Improvement Suggestion:
...

2. Grammar
Level:
Beginner / Intermediate / Advanced

Reason:
...

Detected Grammar Problems:
1. ...

Corrected Sentences:
1. Original: ...
   Correction: ...

Feedback:
...

Improvement Suggestion:
...

3. Pronunciation
Level:
Beginner / Intermediate / Advanced

Reason:
...

Detected Pronunciation Issues:
1. ...

Feedback:
...

Improvement Suggestion:
...

4. Vocabulary
Level:
Beginner / Intermediate / Advanced

Reason:
...

Vocabulary Notes:
- Repeated words:
- Good words used:
- Words to improve:

Feedback:
...

Improvement Suggestion:
...

Final Feedback for Student:
...

Next Practice Task:
...
"""


# # =========================
# # Load Model Once at Startup
# # =========================
model_name = "Qwen/Qwen2-Audio-7B-Instruct"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(
    model_name,
    trust_remote_code=True
)

print("Loading model...")
model = Qwen2AudioForConditionalGeneration.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

model.eval()
print("Model loaded successfully.")


# =========================
# Helper: Download Audio URL
# =========================
def download_audio(audio_url: str) -> str:
    try:
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download audio: {str(e)}"
        )

    content_type = response.headers.get("content-type", "")

    suffix = ".wav"
    if "mpeg" in content_type or audio_url.lower().endswith(".mp3"):
        suffix = ".mp3"
    elif "wav" in content_type or audio_url.lower().endswith(".wav"):
        suffix = ".wav"
    elif "ogg" in content_type or audio_url.lower().endswith(".ogg"):
        suffix = ".ogg"
    elif "webm" in content_type or audio_url.lower().endswith(".webm"):
        suffix = ".webm"
    elif "m4a" in content_type or audio_url.lower().endswith(".m4a"):
        suffix = ".m4a"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(response.content)
    temp_file.close()

    return temp_file.name


# =========================
# Health Check
# =========================
@app.get("/")
def root():
    return {
        "message": "FARIS Speaking Evaluation API is running",
        "model": model_name
    }


# =========================
# Main Endpoint: Audio URL
# =========================
@app.post("/evaluate-url")
def evaluate_audio_url(request: AudioUrlRequest):
    temp_audio_path = None

    try:
        temp_audio_path = download_audio(request.audio_url)

        # Load audio as waveform
        audio, sr = librosa.load(
            temp_audio_path,
            sr=processor.feature_extractor.sampling_rate
        )

        conversation = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "audio_url": request.audio_url
                    },
                    {
                        "type": "text",
                        "text": FARIS_PROMPT
                    }
                ]
            }
        ]

        text = processor.apply_chat_template(
            conversation,
            add_generation_prompt=True,
            tokenize=False
        )

        inputs = processor(
            text=text,
            audio=[audio],
            sampling_rate=sr,
            return_tensors="pt",
            padding=True
        )

        inputs = {
            k: v.to(model.device) if hasattr(v, "to") else v
            for k, v in inputs.items()
        }

        max_new_tokens = request.max_new_tokens or DEFAULT_MAX_NEW_TOKENS

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False
            )

        generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

        response_text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        return {
            "success": True,
            "audio_url": request.audio_url,
            "model": model_name,
            "max_new_tokens": max_new_tokens,
            "result": response_text
        }

    except HTTPException:
        raise

    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(
            status_code=500,
            detail="CUDA out of memory. Try shorter audio or reduce max_new_tokens."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False
    )