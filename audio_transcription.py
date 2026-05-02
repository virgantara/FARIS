import torch
import librosa
from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

model_name = "Qwen/Qwen2-Audio-7B-Instruct"
audio_path = "data/sample.mp3"

processor = AutoProcessor.from_pretrained(
    model_name,
    trust_remote_code=True
)

model = Qwen2AudioForConditionalGeneration.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

# Load audio as waveform
audio, sr = librosa.load(
    audio_path,
    sr=processor.feature_extractor.sampling_rate
)

prompt = """
You are FARIS, an English academic speaking grammar evaluator.

Analyze the student's spoken English from the audio.

First, transcribe the student's speech as accurately as possible.
Then evaluate ONLY the grammar aspect based on this rubric:

Beginner:
- Uses simple sentence patterns (S-V-O)
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

Return the result in this format:

Transcript:
...

Grammar Level:
Beginner / Intermediate / Advanced

Reason:
...

Detected Grammar Problems:
1. ...

Corrected Sentences:
1. Original: ...
   Correction: ...

Feedback for Student:
...

Improvement Suggestion:
...
"""

conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio_url": audio_path},
            {"type": "text", "text": prompt}
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

with torch.no_grad():
    output_ids = model.generate(
        **inputs,
        max_new_tokens=300,
        # max_new_tokens=700,
        do_sample=False,
        temperature=None
    )

generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

response = processor.batch_decode(
    generated_ids,
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False
)[0]

print(response)