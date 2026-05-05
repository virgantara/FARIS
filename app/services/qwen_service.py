import torch
import librosa

from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

from app.config import MODEL_NAME
from app.prompts import FARIS_PROMPT


class QwenAudioService:
    def __init__(self):
        self.model_name = MODEL_NAME

        print("Loading processor...")
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )

        print("Loading model...")
        self.model = Qwen2AudioForConditionalGeneration.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )

        self.model.eval()
        print("Model loaded successfully.")

    def evaluate_audio(
        self,
        audio_path: str,
        audio_url: str = None,
        max_new_tokens: int = 1800
    ) -> str:
        target_sr = self.processor.feature_extractor.sampling_rate

        audio, sr = librosa.load(
            audio_path,
            sr=target_sr,
            mono=True
        )

        conversation = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": FARIS_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "audio_url": audio_url or audio_path
                    },
                    {
                        "type": "text",
                        "text": (
                            "Evaluate this student's spoken English. "
                            "Return the complete strict JSON object. "
                            "Do not return only transcript."
                        )
                    }
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            conversation,
            add_generation_prompt=True,
            tokenize=False
        )

        inputs = self.processor(
            text=text,
            audios=[audio],
            sampling_rate=target_sr,
            return_tensors="pt",
            padding=True
        )

        inputs = {
            k: v.to(self.model.device) if hasattr(v, "to") else v
            for k, v in inputs.items()
        }

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None
            )

        generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

        response_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        return response_text.strip()


qwen_audio_service = QwenAudioService()