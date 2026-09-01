import streamlit as st
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info


# CONFIGURATION & HARDWARE


st.set_page_config(
    page_title="SafeSpace AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.bfloat16 if torch.cuda.is_available() else torch.float32

st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 10% 0%, rgba(52, 211, 153, 0.08), transparent 30%),
                radial-gradient(circle at 90% 10%, rgba(96, 165, 250, 0.07), transparent 30%),
                #090d14;
    color: #e5e7eb;
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #0d121b;
    border-right: 1px solid #1e293b;
}

.sidebar-logo {
    text-align: center;
    padding: 10px 0 20px;
}

.sidebar-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto 10px auto;
    border-radius: 16px;
    background: linear-gradient(135deg, #34d399, #10b981);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.2);
}

.sidebar-title {
    font-size: 19px;
    font-weight: 800;
    color: #f8fafc;
}

.sidebar-subtitle {
    font-size: 12px;
    color: #64748b;
}

/* Custom UI Cards & Badges */
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.page-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #f8fafc;
}

.page-subtitle {
    margin-top: 4px;
    color: #64748b;
    font-size: 14px;
}

.local-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(52, 211, 153, 0.2);
    color: #6ee7b7;
    font-size: 12px;
    font-weight: 600;
}

.local-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
}

.disclaimer {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(245, 158, 11, 0.06);
    border: 1px solid rgba(245, 158, 11, 0.18);
    color: #fcd34d;
    font-size: 13px;
    margin-bottom: 20px;
}

.status-card {
    padding: 14px;
    border-radius: 12px;
    background: #111827;
    border: 1px solid #1e293b;
    margin-bottom: 10px;
}

.badge {
    display: inline-flex;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}

.badge-green {
    color: #6ee7b7;
    background: rgba(16, 185, 129, 0.15);
}

.badge-blue {
    color: #93c5fd;
    background: rgba(59, 130, 246, 0.15);
}

.section-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
}
</style>""",
    unsafe_allow_html=True,
)

# ============================================================
# SESSION STATE & CRISIS FILTER
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "want to die",
    "hurt myself", "self harm", "self-harm"
]

def check_crisis(text):
    text_lower = text.lower()
    if any(k in text_lower for k in CRISIS_KEYWORDS):
        return (
            "I’m really sorry you're going through something this painful.\n\n"
            "Please reach out to a real person who can stay with you and help:\n\n"
            "* **India:** Tele-MANAS: `14416` / `1800-891-4416`\n"
            "* **US/Canada:** `988`\n"
            "* **International:** [Find A Helpline](https://findahelpline.com)"
        )
    return None

SYSTEM_PROMPT = """You are SafeSpace AI, a warm and compassionate wellness companion.
Listen without judgment, validate emotions, and suggest gentle grounding exercises.
You are not a doctor or therapist. Never diagnose medical or psychiatric conditions."""


# MODEL LOADER


@st.cache_resource(show_spinner=False)
def load_model():
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_NAME,
        torch_dtype=DTYPE,
        device_map=DEVICE,
    )
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    return model, processor

def generate_response(messages, max_new_tokens=350):
    model, processor = load_model()
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(DEVICE)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    trimmed_ids = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
    ]
    output_text = processor.batch_decode(
        trimmed_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    return output_text[0]


# SIDEBAR


with st.sidebar:
    st.markdown(
        """<div class="sidebar-logo">
            <div class="sidebar-icon">🌱</div>
            <div class="sidebar-title">SafeSpace AI</div>
            <div class="sidebar-subtitle">Private Local Companion</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.button("💬   Conversation", use_container_width=True):
        st.session_state.page = "Chat"

    if st.button("🩻   Image Analysis", use_container_width=True):
        st.session_state.page = "Image Analysis"

    st.divider()

    device_label = f"Running on {DEVICE.upper()}"
    st.markdown(
        f"""<div class="status-card">
            <span class="badge badge-green">● LOCAL</span>
            <div style="font-weight:700; color:#f8fafc; margin-top:8px;">Qwen2-VL-2B</div>
            <div style="font-size:12px; color:#94a3b8;">{device_label}</div>
        </div>
        <div class="status-card">
            <span class="badge badge-blue">🔒 PRIVATE</span>
            <div style="font-weight:700; color:#f8fafc; margin-top:8px;">No Cloud API</div>
            <div style="font-size:12px; color:#94a3b8;">All weights run on-device</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.button("🗑️   Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# VIEW: CHAT
# ============================================================

if st.session_state.page == "Chat":
    st.markdown(
        """<div class="topbar">
            <div>
                <div class="page-title">SafeSpace</div>
                <div class="page-subtitle">A private space to talk, reflect and breathe.</div>
            </div>
            <div class="local-pill"><span class="local-dot"></span>100% LOCAL</div>
        </div>
        <div class="disclaimer">
            <span>⚠️</span>
            <span><b>Wellness support, not medical care.</b> If you're experiencing a medical emergency, seek professional care.</span>
        </div>""",
        unsafe_allow_html=True,
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Write what's on your mind...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        crisis = check_crisis(user_input)
        if crisis:
            with st.chat_message("assistant"):
                st.markdown(crisis)
            st.session_state.messages.append({"role": "assistant", "content": crisis})
        else:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                try:
                    conversation = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
                    response = generate_response(conversation, max_new_tokens=300)
                    placeholder.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as error:
                    st.error("Inference failed on local hardware.")
                    with st.expander("Technical details"):
                        st.exception(error)

# ============================================================
# VIEW: IMAGE ANALYSIS
# ============================================================

elif st.session_state.page == "Image Analysis":
    st.markdown(
        """<div class="topbar">
            <div>
                <div class="page-title">Image Analysis</div>
                <div class="page-subtitle">Inspect visual data with your local vision model.</div>
            </div>
            <div class="local-pill"><span class="local-dot"></span>LOCAL PROCESSING</div>
        </div>
        <div class="disclaimer">
            <span>⚠️</span>
            <span><b>Educational research prototype.</b> This model does not produce medical diagnoses.</span>
        </div>""",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown(
            """<div class="section-card">
                <b>📷 Upload Image</b>
                <div style="font-size:12px; color:#64748b; margin-top:4px;">Upload PNG, JPG, or WEBP files.</div>
            </div>""",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")

        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, use_container_width=True)

    with col_right:
        st.markdown(
            """<div class="section-card">
                <b>🎯 Inspection Prompt</b>
                <div style="font-size:12px; color:#64748b; margin-top:4px;">Define what you want the vision model to inspect.</div>
            </div>""",
            unsafe_allow_html=True,
        )
        analysis_prompt = st.text_area(
            "Prompt",
            value="Describe the visible features in this image for educational purposes. Discuss clarity, visible structures, and patterns without providing a medical diagnosis.",
            height=140,
            label_visibility="collapsed",
        )

        if uploaded_file and st.button("🔍 Run Analysis", type="primary", use_container_width=True):
            with st.status("Processing image on local hardware...", expanded=True) as status:
                try:
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": analysis_prompt}
                        ]
                    }]
                    output_text = generate_response(messages, max_new_tokens=300)
                    status.update(label="Analysis complete", state="complete")
                    st.markdown(f"""<div class="section-card"><b>AI Output:</b><br><br>{output_text}</div>""", unsafe_allow_html=True)
                except Exception as err:
                    status.update(label="Analysis failed", state="error")
                    st.exception(err)