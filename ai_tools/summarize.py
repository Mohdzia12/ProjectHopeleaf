import torch
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

DTYPE = (
    torch.bfloat16
    if torch.cuda.is_available()
    else torch.float32
)


# ============================================================
# MODEL
# ============================================================

_model = None
_processor = None


def load_model():

    global _model
    global _processor

    if _model is None or _processor is None:

        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype=DTYPE,
            device_map=DEVICE,
        )

        _processor = AutoProcessor.from_pretrained(
            MODEL_NAME
        )

    return _model, _processor


# ============================================================
# PATIENT SUMMARY
# ============================================================

def summarize_patient_reason(reason):

    if not reason or not reason.strip():
        return ""

    model, processor = load_model()


    prompt = f"""
You are an assistant helping a doctor review a patient's appointment request.

Create a detailed but concise clinical-style summary of ONLY what the patient
reported.

The summary is for information organization and must NOT be treated as a
medical diagnosis.

Extract and organize the information into these areas when available:

1. Main concern
2. Duration or onset
3. Symptoms mentioned
4. Severity or frequency, if the patient described it
5. Triggers, circumstances, or patterns mentioned
6. Factors that improve or worsen the symptoms, if mentioned
7. Other relevant information explicitly provided by the patient

IMPORTANT RULES:

- Do NOT diagnose the patient.
- Do NOT suggest treatment or medication.
- Do NOT recommend a medical condition as an explanation.
- Do NOT invent symptoms, duration, severity, causes, or history.
- Do NOT assume information that the patient did not provide.
- Preserve uncertainty when the patient's statement is unclear.
- Do not exaggerate the patient's symptoms.
- Use professional, neutral language.
- Keep the summary around 3-5 sentences.
- If a category is not mentioned, simply leave it out rather than writing
  "not provided."
- The summary should make it easy for a doctor to quickly understand why
  the patient requested the appointment.

Patient's description:

{reason}
"""


    # ========================================================
    # QWEN MESSAGE
    # ========================================================

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]


    # ========================================================
    # PREPARE INPUT
    # ========================================================

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )


    image_inputs, video_inputs = process_vision_info(
        messages
    )


    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(DEVICE)


    # ========================================================
    # GENERATE
    # ========================================================

    with torch.no_grad():

        generated_ids = model.generate(
            **inputs,
            max_new_tokens=220,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
        )


    # ========================================================
    # REMOVE INPUT TOKENS
    # ========================================================

    trimmed_ids = [
        output_ids[len(input_ids):]
        for input_ids, output_ids
        in zip(
            inputs["input_ids"],
            generated_ids
        )
    ]


    # ========================================================
    # DECODE
    # ========================================================

    output_text = processor.batch_decode(
        trimmed_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )


    return output_text[0].strip()