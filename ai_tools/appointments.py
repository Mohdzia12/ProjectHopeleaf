# import streamlit as st
# import torch
# from pymongo import MongoClient
# from datetime import datetime, date
# from transformers import AutoProcessor, Qwen2VLForConditionalGeneration


# # ============================================================
# # CONFIG
# # ============================================================

# MONGODB_URI = "mongodb://127.0.0.1:27017/hopeleaf"
# MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# DTYPE = (
#     torch.bfloat16
#     if torch.cuda.is_available()
#     else torch.float32
# )

# st.set_page_config(
#     page_title="HopeLeaf Appointments",
#     page_icon="📅",
#     layout="centered",
# )


# # ============================================================
# # DATABASE
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def get_database():

#     client = MongoClient(MONGODB_URI)

#     client.admin.command("ping")

#     return client["hopeleaf"]


# try:

#     db = get_database()

#     users_collection = db["users"]

#     appointments_collection = db["appointments"]

# except Exception as error:

#     st.error("Could not connect to HopeLeaf database.")

#     st.code(str(error))

#     st.stop()


# # ============================================================
# # QWEN MODEL
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def load_model():

#     model = Qwen2VLForConditionalGeneration.from_pretrained(
#         MODEL_NAME,
#         torch_dtype=DTYPE,
#         device_map=DEVICE,
#     )

#     processor = AutoProcessor.from_pretrained(
#         MODEL_NAME
#     )

#     model.eval()

#     return model, processor


# # ============================================================
# # GENERATE AI PATIENT SUMMARY
# # ============================================================

# def generate_patient_summary(patient_reason):

#     if not patient_reason or not patient_reason.strip():

#         return (
#             "The patient did not provide a description "
#             "of their concern."
#         )

#     model, processor = load_model()

#     system_prompt = """
# You are HopeLeaf's clinical documentation assistant.

# Your task is to convert a patient's own description
# into a clear, natural, professional patient-reported
# summary for a doctor.

# IMPORTANT RULES:

# 1. Only use information explicitly provided by the patient.
# 2. Never invent symptoms.
# 3. Never invent severity.
# 4. Never invent duration.
# 5. Never invent medical history.
# 6. Never invent medications.
# 7. Never invent allergies.
# 8. Never diagnose a disease.
# 9. Never recommend treatment or medication.
# 10. Never make clinical conclusions.

# The summary should sound like a human-written clinical
# documentation note, not a checklist.

# Begin naturally with:

# "The patient reports..."

# Describe, when available:

# - what the patient is feeling
# - the main complaint
# - specific symptoms
# - location of symptoms
# - type/character of discomfort
# - onset
# - duration
# - frequency
# - severity
# - numeric severity such as 7/10 if explicitly stated
# - associated symptoms
# - things that make symptoms better or worse
# - other relevant information explicitly mentioned

# If the patient gives a severity score, preserve it.

# For example:

# "The patient reports abdominal aching for the past
# three days, with intermittent episodes of discomfort
# rated 6/10."

# Do NOT change the patient's reported severity.

# After the summary, provide a section:

# Points to clarify

# Include 3-6 concise questions that the doctor may want
# to clarify during the consultation.

# Only ask questions about information that was not already
# clearly provided by the patient.

# Return plain text only.

# Do not return JSON.

# Do not provide a diagnosis.
# Do not provide treatment advice.
# """

#     user_prompt = f"""
# Patient's own description:

# {patient_reason.strip()}

# Create a natural patient-reported clinical summary
# for the treating doctor.
# """

#     messages = [

#         {
#             "role": "system",
#             "content": system_prompt,
#         },

#         {
#             "role": "user",
#             "content": user_prompt,
#         }

#     ]

#     text = processor.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True,
#     )

#     inputs = processor(
#         text=[text],
#         padding=True,
#         return_tensors="pt",
#     )

#     inputs = {
#         key: value.to(DEVICE)
#         if hasattr(value, "to")
#         else value

#         for key, value in inputs.items()
#     }

#     with torch.no_grad():

#         generated_ids = model.generate(

#             **inputs,

#             max_new_tokens=450,

#             do_sample=True,

#             temperature=0.4,

#             top_p=0.85,

#             repetition_penalty=1.05,
#         )

#     input_ids = inputs["input_ids"]

#     trimmed_ids = [

#         output_ids[len(input_ids[index]):]

#         for index, output_ids
#         in enumerate(generated_ids)

#     ]

#     output_text = processor.batch_decode(

#         trimmed_ids,

#         skip_special_tokens=True,

#         clean_up_tokenization_spaces=False,
#     )

#     summary = output_text[0].strip()

#     if not summary:

#         return (
#             "The patient provided a concern, but "
#             "the AI summary could not be generated."
#         )

#     return summary


# # ============================================================
# # HEADER
# # ============================================================

# st.title("📅 HopeLeaf Appointments")

# st.write(
#     "Book an appointment with a registered HopeLeaf doctor."
# )

# st.divider()


# # ============================================================
# # AI STATUS
# # ============================================================

# with st.expander(
#     "AI Summary Engine",
#     expanded=False
# ):

#     st.write(
#         f"**Model:** {MODEL_NAME}"
#     )

#     st.write(
#         f"**Device:** {DEVICE.upper()}"
#     )

#     st.write(
#         "**Processing:** Local Qwen model"
#     )


# # ============================================================
# # GET DOCTORS
# # ============================================================

# doctors = list(

#     users_collection.find(

#         {
#             "role": "doctor"
#         },

#         {
#             "_id": 1,
#             "name": 1,
#             "email": 1
#         }
#     )
# )


# if not doctors:

#     st.warning(
#         "No doctors are registered yet."
#     )

#     st.stop()


# doctor_options = {

#     f"{doctor['name']} ({doctor['email']})":
#         doctor

#     for doctor in doctors
# }


# # ============================================================
# # BOOKING FORM
# # ============================================================

# st.subheader(
#     "Book an Appointment"
# )


# selected_doctor_label = st.selectbox(

#     "Select Doctor",

#     list(
#         doctor_options.keys()
#     )
# )


# selected_doctor = doctor_options[
#     selected_doctor_label
# ]


# # ============================================================
# # PATIENT INFORMATION
# # ============================================================

# st.markdown(
#     "### Patient Information"
# )


# patient_email = st.text_input(

#     "Patient Email",

#     placeholder="patient@hopeleaf.com"
# )


# # ============================================================
# # APPOINTMENT DETAILS
# # ============================================================

# st.markdown(
#     "### Appointment Details"
# )


# appointment_date = st.date_input(

#     "Appointment Date",

#     min_value=date.today()
# )


# appointment_time = st.time_input(

#     "Appointment Time"
# )


# reason = st.text_area(

#     "What are you experiencing?",

#     placeholder=(
#         "Describe what you are feeling in your own words. "
#         "For example: I have been feeling an ache in my "
#         "abdomen for two days and it gets worse after eating..."
#     ),

#     height=180
# )


# st.caption(

#     "Your description will be analyzed by HopeLeaf's "
#     "local Qwen AI and summarized for the doctor."
# )


# # ============================================================
# # CONFIRM APPOINTMENT
# # ============================================================

# if st.button(

#     "Confirm Appointment",

#     type="primary",

#     use_container_width=True
# ):

#     # --------------------------------------------------------
#     # VALIDATE PATIENT EMAIL
#     # --------------------------------------------------------

#     if not patient_email.strip():

#         st.error(
#             "Please enter your patient email."
#         )

#         st.stop()


#     # --------------------------------------------------------
#     # FIND PATIENT
#     # --------------------------------------------------------

#     patient = users_collection.find_one(

#         {
#             "email": patient_email.strip().lower(),

#             "role": "patient"
#         }
#     )


#     if not patient:

#         st.error(
#             "No patient account was found with this email."
#         )

#         st.info(

#             "Please enter the same email address "
#             "used for your HopeLeaf patient account."
#         )

#         st.stop()


#     # --------------------------------------------------------
#     # VALIDATE REASON
#     # --------------------------------------------------------

#     if not reason.strip():

#         st.error(
#             "Please describe what you are experiencing "
#             "before booking the appointment."
#         )

#         st.stop()


#     # --------------------------------------------------------
#     # APPOINTMENT DATETIME
#     # --------------------------------------------------------

#     appointment_datetime = datetime.combine(

#         appointment_date,

#         appointment_time
#     )


#     # ========================================================
#     # QWEN SUMMARY
#     # ========================================================

#     with st.spinner(

#         "Qwen is analyzing the patient's description..."
#     ):

#         try:

#             ai_summary = generate_patient_summary(
#                 reason
#             )

#         except Exception as error:

#             st.error(
#                 "Qwen could not generate the patient summary."
#             )

#             st.exception(error)

#             st.stop()


#     # ========================================================
#     # SAVE APPOINTMENT
#     # ========================================================

#     appointment = {

#         # Patient
#         "patient_id": patient["_id"],

#         "patient_name": patient["name"],

#         "patient_email": patient["email"],


#         # Doctor
#         "doctor_id": selected_doctor["_id"],

#         "doctor_name": selected_doctor["name"],

#         "doctor_email": selected_doctor["email"],


#         # Appointment
#         "date": appointment_date.isoformat(),

#         "time": appointment_time.strftime("%H:%M"),

#         "appointment_datetime":
#             appointment_datetime,


#         # Original patient description
#         "reason": reason.strip(),


#         # Qwen generated summary
#         "ai_summary": ai_summary,


#         # Appointment status
#         "status": "scheduled",


#         # Created timestamp
#         "created_at": datetime.utcnow()
#     }


#     try:

#         result = appointments_collection.insert_one(
#             appointment
#         )

#     except Exception as error:

#         st.error(
#             "Could not save the appointment."
#         )

#         st.exception(error)

#         st.stop()


#     # ========================================================
#     # SUCCESS
#     # ========================================================

#     st.success(

#         f"Appointment booked with "
#         f"Dr. {selected_doctor['name']}."
#     )


#     st.divider()


#     # ========================================================
#     # CONFIRMATION
#     # ========================================================

#     st.subheader(
#         "Appointment Confirmed"
#     )


#     col1, col2 = st.columns(2)


#     with col1:

#         st.write("**Patient**")

#         st.write(
#             patient["name"]
#         )

#         st.write("**Doctor**")

#         st.write(
#             f"Dr. {selected_doctor['name']}"
#         )


#     with col2:

#         st.write("**Date**")

#         st.write(

#             appointment_date.strftime(
#                 "%d %B %Y"
#             )
#         )

#         st.write("**Time**")

#         st.write(

#             appointment_time.strftime(
#                 "%H:%M"
#             )
#         )


#     # ========================================================
#     # PATIENT DESCRIPTION
#     # ========================================================

#     st.subheader(
#         "Patient's Description"
#     )


#     st.info(
#         reason.strip()
#     )


#     # ========================================================
#     # AI SUMMARY
#     # ========================================================

#     st.subheader(
#         "AI Patient Summary"
#     )


#     st.caption(
#         "AI-generated assistance for clinical review"
#     )


#     st.markdown(
#         ai_summary
#     )


#     st.warning(

#         "This summary is generated from the patient's "
#         "own description using a local Qwen model. "
#         "It is not a diagnosis, clinical conclusion, "
#         "or treatment recommendation."
#     )


#     # ========================================================
#     # APPOINTMENT REFERENCE
#     # ========================================================

#     with st.expander(
#         "Appointment Reference"
#     ):

#         st.write(
#             "Appointment ID"
#         )

#         st.code(
#             str(result.inserted_id)
#         )
# import streamlit as st
# import torch
# import time

# from pymongo import MongoClient
# from datetime import datetime, date
# from transformers import AutoProcessor, Qwen2VLForConditionalGeneration


# # ============================================================
# # CONFIG
# # ============================================================

# MONGODB_URI = "mongodb://127.0.0.1:27017/hopeleaf"

# MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# if torch.cuda.is_available():
#     DTYPE = torch.bfloat16
# else:
#     DTYPE = torch.float32


# st.set_page_config(
#     page_title="HopeLeaf Appointments",
#     page_icon="📅",
#     layout="centered",
# )


# # ============================================================
# # DATABASE
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def get_database():

#     client = MongoClient(MONGODB_URI)

#     client.admin.command("ping")

#     return client["hopeleaf"]


# try:

#     db = get_database()

#     users_collection = db["users"]

#     appointments_collection = db["appointments"]

# except Exception as error:

#     st.error("Could not connect to HopeLeaf database.")

#     st.code(str(error))

#     st.stop()


# # ============================================================
# # QWEN MODEL
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def load_model():

#     start_time = time.time()

#     model = Qwen2VLForConditionalGeneration.from_pretrained(
#         MODEL_NAME,
#         torch_dtype=DTYPE,
#         device_map="auto"
#     )

#     processor = AutoProcessor.from_pretrained(
#         MODEL_NAME
#     )

#     model.eval()

#     load_time = time.time() - start_time

#     return model, processor, load_time


# # ============================================================
# # GENERATE PATIENT SUMMARY
# # ============================================================

# def generate_patient_summary(patient_reason):

#     if not patient_reason or not patient_reason.strip():

#         return (
#             "The patient did not provide a description "
#             "of their concern."
#         )


#     # --------------------------------------------------------
#     # LOAD QWEN
#     # --------------------------------------------------------

#     model, processor, load_time = load_model()


#     # --------------------------------------------------------
#     # SYSTEM PROMPT
#     # --------------------------------------------------------

#     system_prompt = """
# You are HopeLeaf's clinical documentation assistant.

# Your job is to convert a patient's own description into
# a concise, natural, professional patient-reported summary
# for a doctor.

# This is documentation assistance only.

# STRICT RULES:

# 1. Use ONLY information explicitly stated by the patient.

# 2. NEVER invent symptoms.

# 3. NEVER invent severity.

# 4. NEVER invent duration.

# 5. NEVER invent onset.

# 6. NEVER invent location.

# 7. NEVER invent frequency.

# 8. NEVER invent associated symptoms.

# 9. NEVER invent medical history.

# 10. NEVER invent medications.

# 11. NEVER invent allergies.

# 12. NEVER diagnose a disease.

# 13. NEVER provide treatment advice.

# 14. NEVER recommend medication.

# 15. NEVER make a clinical conclusion.

# 16. NEVER assume something just because it is common.

# 17. If information is missing, leave it unspecified.

# 18. If the patient gives a numeric severity such as
#     7/10, preserve the exact severity.

# 19. If the patient gives words describing severity such as
#     mild, moderate, severe, unbearable, etc., preserve
#     those words.

# 20. Do not convert words into numbers.

# 21. Do not convert numbers into different severity levels.

# 22. Do not change the patient's meaning.

# 23. Do not exaggerate the patient's symptoms.

# 24. Do not minimize the patient's symptoms.


# SUMMARY REQUIREMENTS:

# Write a natural clinical documentation summary.

# Start with:

# "The patient reports..."

# Include relevant information when explicitly provided:

# - main complaint
# - symptoms
# - symptom location
# - symptom type or character
# - onset
# - duration
# - frequency
# - severity
# - numeric severity
# - associated symptoms
# - triggers
# - relieving factors
# - worsening factors
# - other relevant patient-provided information


# IMPORTANT:

# Do NOT turn the summary into a checklist.

# Do NOT add information that the patient did not say.

# Keep the summary concise.

# Usually use 1-3 sentences.


# CLARIFICATION REQUIREMENTS:

# After the summary, create:

# Points to clarify

# Ask only clinically useful questions about information
# that is genuinely missing.

# Use 3-5 questions maximum.

# Prioritize questions in this order when relevant:

# 1. Location of the symptom
# 2. Onset and duration
# 3. Severity
# 4. Frequency or pattern
# 5. Factors that make it better or worse
# 6. Important associated symptoms

# However:

# DO NOT ask about information that the patient already provided.

# For example:

# If the patient already said:
# "I have chest pain for two days."

# DO NOT ask:

# "How long has the pain been present?"

# Instead ask about missing information such as:

# "Where exactly is the chest pain located?"
# "How severe is the pain?"
# "Does anything make the pain better or worse?"

# If the patient already provided severity,
# DO NOT ask for severity again.

# If the patient already provided location,
# DO NOT ask for location again.

# If the patient already provided duration,
# DO NOT ask for duration again.

# Questions must be specific to the patient's complaint.

# Do not generate generic questions unrelated to the complaint.

# If very little information is available, ask the most
# important missing questions rather than generating many
# questions.

# Return plain text only.

# Use exactly this structure:

# The patient reports [summary].

# Points to clarify

# 1. [question]
# 2. [question]
# 3. [question]

# Do not include diagnosis.

# Do not include treatment.

# Do not include medical advice.
# """


#     # --------------------------------------------------------
#     # USER PROMPT
#     # --------------------------------------------------------

#     user_prompt = f"""
# Patient's own description:

# {patient_reason.strip()}

# Analyze the patient's description carefully.

# First create a faithful patient-reported clinical summary.

# Then identify only the most important missing information
# that the doctor may want to clarify.

# Do not invent information.
# """


#     # --------------------------------------------------------
#     # CHAT TEMPLATE
#     # --------------------------------------------------------

#     messages = [

#         {
#             "role": "system",
#             "content": system_prompt
#         },

#         {
#             "role": "user",
#             "content": user_prompt
#         }

#     ]


#     # --------------------------------------------------------
#     # PREPARE INPUT
#     # --------------------------------------------------------

#     text = processor.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True
#     )


#     inputs = processor(
#         text=[text],
#         padding=True,
#         return_tensors="pt"
#     )


#     # --------------------------------------------------------
#     # MOVE INPUTS TO MODEL DEVICE
#     # --------------------------------------------------------

#     if torch.cuda.is_available():

#         inputs = {
#             key: value.to("cuda")
#             if hasattr(value, "to")
#             else value
#             for key, value in inputs.items()
#         }

#     else:

#         inputs = {
#             key: value.to("cpu")
#             if hasattr(value, "to")
#             else value
#             for key, value in inputs.items()
#         }


#     # --------------------------------------------------------
#     # GENERATE
#     # --------------------------------------------------------

#     generation_start = time.time()

#     with torch.no_grad():

#         generated_ids = model.generate(

#             **inputs,

#             max_new_tokens=350,

#             do_sample=False,

#             repetition_penalty=1.08,

#         )


#     generation_time = time.time() - generation_start


#     # --------------------------------------------------------
#     # REMOVE INPUT TOKENS
#     # --------------------------------------------------------

#     input_ids = inputs["input_ids"]

#     trimmed_ids = [

#         output_ids[len(input_ids[index]):]

#         for index, output_ids
#         in enumerate(generated_ids)

#     ]


#     # --------------------------------------------------------
#     # DECODE
#     # --------------------------------------------------------

#     output_text = processor.batch_decode(

#         trimmed_ids,

#         skip_special_tokens=True,

#         clean_up_tokenization_spaces=True

#     )


#     if not output_text:

#         return (
#             "The patient provided a concern, but "
#             "the AI summary could not be generated."
#         )


#     summary = output_text[0].strip()


#     if not summary:

#         return (
#             "The patient provided a concern, but "
#             "the AI summary could not be generated."
#         )


#     return summary


# # ============================================================
# # HEADER
# # ============================================================

# st.title("📅 HopeLeaf Appointments")

# st.write(
#     "Book an appointment with a registered HopeLeaf doctor."
# )

# st.divider()


# # ============================================================
# # AI STATUS
# # ============================================================

# with st.expander(
#     "AI Summary Engine",
#     expanded=False
# ):

#     st.write(
#         f"**Model:** {MODEL_NAME}"
#     )

#     st.write(
#         f"**Device:** {DEVICE.upper()}"
#     )

#     if torch.cuda.is_available():

#         st.success(
#             "Qwen will run using the NVIDIA GPU."
#         )

#         try:

#             st.write(
#                 f"**GPU:** {torch.cuda.get_device_name(0)}"
#             )

#         except Exception:
#             pass

#     else:

#         st.warning(
#             "CUDA is not available. Qwen will run on CPU."
#         )

#     st.write(
#         "**Processing:** Local Qwen AI"
#     )


# # ============================================================
# # GET DOCTORS
# # ============================================================

# doctors = list(
#     users_collection.find(
#         {
#             "role": "doctor"
#         },
#         {
#             "_id": 1,
#             "name": 1,
#             "email": 1
#         }
#     )
# )


# if not doctors:

#     st.warning(
#         "No doctors are registered yet."
#     )

#     st.stop()


# doctor_options = {

#     f"{doctor['name']} ({doctor['email']})":
#         doctor

#     for doctor in doctors

# }


# # ============================================================
# # BOOKING FORM
# # ============================================================

# st.subheader(
#     "Book an Appointment"
# )


# selected_doctor_label = st.selectbox(

#     "Select Doctor",

#     list(
#         doctor_options.keys()
#     )

# )


# selected_doctor = doctor_options[
#     selected_doctor_label
# ]


# # ============================================================
# # PATIENT INFORMATION
# # ============================================================

# st.markdown(
#     "### Patient Information"
# )


# patient_email = st.text_input(

#     "Patient Email",

#     placeholder="patient@hopeleaf.com"

# )


# # ============================================================
# # APPOINTMENT DETAILS
# # ============================================================

# st.markdown(
#     "### Appointment Details"
# )


# appointment_date = st.date_input(

#     "Appointment Date",

#     min_value=date.today()

# )


# appointment_time = st.time_input(

#     "Appointment Time"

# )


# reason = st.text_area(

#     "What are you experiencing?",

#     placeholder=(
#         "Describe what you are feeling in your own words. "
#         "For example: I have been feeling an ache in my "
#         "abdomen for two days and it gets worse after eating..."
#     ),

#     height=180

# )


# st.caption(

#     "Your description will be analyzed by HopeLeaf's "
#     "local Qwen AI and summarized for the doctor."

# )


# # ============================================================
# # CONFIRM APPOINTMENT
# # ============================================================

# if st.button(

#     "Confirm Appointment",

#     type="primary",

#     use_container_width=True

# ):

#     # --------------------------------------------------------
#     # VALIDATE PATIENT EMAIL
#     # --------------------------------------------------------

#     if not patient_email.strip():

#         st.error(
#             "Please enter your patient email."
#         )

#         st.stop()


#     # --------------------------------------------------------
#     # FIND PATIENT
#     # --------------------------------------------------------

#     patient = users_collection.find_one(

#         {
#             "email": patient_email.strip().lower(),

#             "role": "patient"
#         }

#     )


#     if not patient:

#         st.error(

#             "No patient account was found with this email."

#         )

#         st.info(

#             "Please enter the same email address "
#             "used for your HopeLeaf patient account."

#         )

#         st.stop()


#     # --------------------------------------------------------
#     # VALIDATE REASON
#     # --------------------------------------------------------

#     if not reason.strip():

#         st.error(

#             "Please describe what you are experiencing "
#             "before booking the appointment."

#         )

#         st.stop()


#     # --------------------------------------------------------
#     # APPOINTMENT DATETIME
#     # --------------------------------------------------------

#     appointment_datetime = datetime.combine(

#         appointment_date,

#         appointment_time

#     )


#     # ========================================================
#     # QWEN SUMMARY
#     # ========================================================

#     with st.spinner(
#         "Qwen is analyzing the patient's description..."
#     ):

#         try:

#             qwen_start = time.time()

#             ai_summary = generate_patient_summary(
#                 reason
#             )

#             qwen_total_time = time.time() - qwen_start

#         except Exception as error:

#             st.error(
#                 "Qwen could not generate the patient summary."
#             )

#             st.exception(error)

#             st.stop()


#     # ========================================================
#     # SAVE APPOINTMENT
#     # ========================================================

#     appointment = {

#         # ----------------------------------------------------
#         # Patient
#         # ----------------------------------------------------

#         "patient_id": patient["_id"],

#         "patient_name": patient["name"],

#         "patient_email": patient["email"],


#         # ----------------------------------------------------
#         # Doctor
#         # ----------------------------------------------------

#         "doctor_id": selected_doctor["_id"],

#         "doctor_name": selected_doctor["name"],

#         "doctor_email": selected_doctor["email"],


#         # ----------------------------------------------------
#         # Appointment
#         # ----------------------------------------------------

#         "date": appointment_date.isoformat(),

#         "time": appointment_time.strftime("%H:%M"),

#         "appointment_datetime":
#             appointment_datetime,


#         # ----------------------------------------------------
#         # Original patient description
#         # ----------------------------------------------------

#         "reason": reason.strip(),


#         # ----------------------------------------------------
#         # Qwen generated summary
#         # ----------------------------------------------------

#         "ai_summary": ai_summary,


#         # ----------------------------------------------------
#         # Appointment status
#         # ----------------------------------------------------

#         "status": "scheduled",


#         # ----------------------------------------------------
#         # Created timestamp
#         # ----------------------------------------------------

#         "created_at": datetime.utcnow()

#     }


#     # ========================================================
#     # DATABASE SAVE
#     # ========================================================

#     try:

#         result = appointments_collection.insert_one(
#             appointment
#         )

#     except Exception as error:

#         st.error(
#             "Could not save the appointment."
#         )

#         st.exception(error)

#         st.stop()


#     # ========================================================
#     # SUCCESS
#     # ========================================================

#     st.success(

#         f"Appointment booked with "
#         f"Dr. {selected_doctor['name']}."

#     )


#     st.divider()


#     # ========================================================
#     # CONFIRMATION
#     # ========================================================

#     st.subheader(
#         "Appointment Confirmed"
#     )


#     col1, col2 = st.columns(2)


#     with col1:

#         st.write("**Patient**")

#         st.write(
#             patient["name"]
#         )

#         st.write("**Doctor**")

#         st.write(
#             f"Dr. {selected_doctor['name']}"
#         )


#     with col2:

#         st.write("**Date**")

#         st.write(

#             appointment_date.strftime(
#                 "%d %B %Y"
#             )

#         )

#         st.write("**Time**")

#         st.write(

#             appointment_time.strftime(
#                 "%H:%M"
#             )

#         )


#     # ========================================================
#     # PATIENT DESCRIPTION
#     # ========================================================

#     st.subheader(
#         "Patient's Description"
#     )


#     st.info(
#         reason.strip()
#     )


#     # ========================================================
#     # AI SUMMARY
#     # ========================================================

#     st.subheader(
#         "AI Patient Summary"
#     )


#     st.caption(
#         "AI-generated assistance for clinical review"
#     )


#     st.markdown(
#         ai_summary
#     )


#     # ========================================================
#     # AI PROCESSING INFORMATION
#     # ========================================================

#     with st.expander(
#         "Qwen Processing Information"
#     ):

#         st.write(
#             f"**Model:** {MODEL_NAME}"
#         )

#         st.write(
#             f"**Device:** {DEVICE.upper()}"
#         )

#         st.write(
#             f"**Generation time:** "
#             f"{qwen_total_time:.2f} seconds"
#         )

#         st.success(
#             "Summary generated locally using Qwen."
#         )


#     # ========================================================
#     # SAFETY NOTICE
#     # ========================================================

#     st.warning(

#         "This summary is generated from the patient's "
#         "own description using a local Qwen model. "
#         "It is not a diagnosis, clinical conclusion, "
#         "or treatment recommendation."

#     )


#     # ========================================================
#     # APPOINTMENT REFERENCE
#     # ========================================================

#     with st.expander(
#         "Appointment Reference"
#     ):

#         st.write(
#             "Appointment ID"
#         )

#         st.code(
#             str(result.inserted_id)
#         )

# import streamlit as st
# import torch
# import time

# from pymongo import MongoClient
# from datetime import datetime, date
# from transformers import AutoProcessor, Qwen2VLForConditionalGeneration


# # ============================================================
# # CONFIG
# # ============================================================

# MONGODB_URI = "mongodb://127.0.0.1:27017/hopeleaf"

# MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"

# # ------------------------------------------------------------
# # DEVICE
# # ------------------------------------------------------------

# if torch.cuda.is_available():
#     DEVICE = "cuda"
#     DTYPE = torch.bfloat16
# else:
#     DEVICE = "cpu"
#     DTYPE = torch.float32


# st.set_page_config(
#     page_title="HopeLeaf Appointments",
#     page_icon="📅",
#     layout="centered"
# )


# # ============================================================
# # DATABASE
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def get_database():

#     client = MongoClient(MONGODB_URI)

#     client.admin.command("ping")

#     return client["hopeleaf"]


# try:

#     db = get_database()

#     users_collection = db["users"]

#     appointments_collection = db["appointments"]

# except Exception as error:

#     st.error("Could not connect to HopeLeaf database.")

#     st.code(str(error))

#     st.stop()


# # ============================================================
# # QWEN MODEL
# # ============================================================

# @st.cache_resource(show_spinner=False)
# def load_model():

#     start_time = time.time()

#     print()
#     print("========================================")
#     print("HopeLeaf Qwen AI")
#     print("========================================")

#     print("Model:", MODEL_NAME)

#     print("CUDA available:", torch.cuda.is_available())

#     # --------------------------------------------------------
#     # GPU
#     # --------------------------------------------------------

#     if torch.cuda.is_available():

#         gpu_name = torch.cuda.get_device_name(0)

#         print("GPU:", gpu_name)

#         print("Loading Qwen directly onto GPU...")

#         try:

#             model = Qwen2VLForConditionalGeneration.from_pretrained(

#                 MODEL_NAME,

#                 torch_dtype=DTYPE

#             )

#             model = model.to("cuda")

#             processor = AutoProcessor.from_pretrained(
#                 MODEL_NAME
#             )

#         except Exception as error:

#             print("Qwen GPU loading failed.")

#             print(error)

#             raise error

#     # --------------------------------------------------------
#     # CPU
#     # --------------------------------------------------------

#     else:

#         print("CUDA is not available.")

#         print("Loading Qwen on CPU...")

#         try:

#             model = Qwen2VLForConditionalGeneration.from_pretrained(

#                 MODEL_NAME,

#                 torch_dtype=torch.float32

#             )

#             model = model.to("cpu")

#             processor = AutoProcessor.from_pretrained(
#                 MODEL_NAME
#             )

#         except Exception as error:

#             print("Qwen CPU loading failed.")

#             print(error)

#             raise error

#     # --------------------------------------------------------
#     # EVALUATION MODE
#     # --------------------------------------------------------

#     model.eval()

#     load_time = time.time() - start_time

#     print("----------------------------------------")

#     print("Qwen loaded successfully.")

#     print(
#         f"Model loading time: {load_time:.2f} seconds"
#     )

#     print(
#         "Running device:",
#         DEVICE.upper()
#     )

#     print("========================================")
#     print()

#     return model, processor, load_time


# # ============================================================
# # GENERATE PATIENT SUMMARY
# # ============================================================

# def generate_patient_summary(patient_reason):

#     # --------------------------------------------------------
#     # EMPTY DESCRIPTION
#     # --------------------------------------------------------

#     if not patient_reason:

#         return (
#             "The patient did not provide a description "
#             "of their concern."
#         )

#     patient_reason = patient_reason.strip()

#     if not patient_reason:

#         return (
#             "The patient did not provide a description "
#             "of their concern."
#         )


#     # --------------------------------------------------------
#     # LOAD QWEN
#     # --------------------------------------------------------

#     model, processor, model_load_time = load_model()


#     # --------------------------------------------------------
#     # SYSTEM PROMPT
#     # --------------------------------------------------------

#     system_prompt = """
# You are HopeLeaf's clinical documentation assistant.

# Your task is to convert a patient's own description
# into a clear, concise, natural, professional
# patient-reported summary for a doctor.

# This is documentation assistance only.

# STRICT RULES:

# 1. ONLY use information explicitly provided by the patient.

# 2. NEVER invent symptoms.

# 3. NEVER invent severity.

# 4. NEVER invent duration.

# 5. NEVER invent onset.

# 6. NEVER invent location.

# 7. NEVER invent frequency.

# 8. NEVER invent triggers.

# 9. NEVER invent relieving factors.

# 10. NEVER invent worsening factors.

# 11. NEVER invent associated symptoms.

# 12. NEVER invent medical history.

# 13. NEVER invent medications.

# 14. NEVER invent allergies.

# 15. NEVER diagnose a disease.

# 16. NEVER provide treatment advice.

# 17. NEVER recommend medication.

# 18. NEVER make a clinical conclusion.

# 19. NEVER assume information that was not stated.

# 20. NEVER exaggerate symptoms.

# 21. NEVER minimize symptoms.

# 22. Preserve the patient's meaning.

# 23. If the patient gives a numeric severity,
#     preserve the exact number.

# 24. If the patient says "mild", "moderate", "severe",
#     "very severe", "unbearable", etc., preserve
#     those words exactly in meaning.

# 25. Never convert a verbal severity into a number.

# 26. Never convert a number into a different severity.

# 27. If information is missing, do not invent it.


# SUMMARY:

# Write a natural clinical documentation summary.

# Start with:

# "The patient reports..."

# Include information ONLY when it was provided:

# - main complaint
# - symptoms
# - location
# - type or character of symptoms
# - onset
# - duration
# - frequency
# - severity
# - numeric severity
# - associated symptoms
# - triggers
# - relieving factors
# - worsening factors
# - other relevant information


# The summary should normally be 1-3 sentences.

# Do not turn the summary into a checklist.

# Do not repeat the patient's sentence unnecessarily.


# POINTS TO CLARIFY:

# After the summary, create:

# Points to clarify

# Ask 3-5 concise questions about important information
# that is genuinely missing.

# Prioritize:

# 1. Location
# 2. Onset and duration
# 3. Severity
# 4. Frequency or pattern
# 5. Factors that make symptoms better or worse
# 6. Important associated symptoms

# BUT:

# Do NOT ask about information that the patient
# already clearly provided.

# For example:

# Patient:
# "I have chest pain for two days."

# Do NOT ask:

# "When did the pain start?"

# Do NOT ask:

# "How long have you had the pain?"

# Instead ask about information that is missing, such as:

# "Where exactly is the chest pain located?"

# "How severe is the pain?"

# "Does anything make the pain better or worse?"

# If location is already provided,
# do not ask about location.

# If duration is already provided,
# do not ask about duration.

# If severity is already provided,
# do not ask about severity.

# If a symptom has no obvious useful clarification,
# do not create an unnecessary generic question.

# Questions should be relevant to the patient's
# specific complaint.

# Do not generate generic questions simply to fill space.

# Return plain text only.

# Use exactly this structure:

# The patient reports [summary].

# Points to clarify

# 1. [question]
# 2. [question]
# 3. [question]

# Do not provide a diagnosis.

# Do not provide treatment.

# Do not provide medical advice.
# """


#     # --------------------------------------------------------
#     # USER PROMPT
#     # --------------------------------------------------------

#     user_prompt = f"""
# Patient's own description:

# {patient_reason}

# Carefully analyze only what the patient actually said.

# Create a faithful patient-reported clinical summary.

# Then provide only the most important missing
# information that the doctor may want to clarify.

# Do not invent anything.
# """


#     # --------------------------------------------------------
#     # CHAT MESSAGES
#     # --------------------------------------------------------

#     messages = [

#         {
#             "role": "system",

#             "content": system_prompt
#         },

#         {
#             "role": "user",

#             "content": user_prompt
#         }

#     ]


#     # --------------------------------------------------------
#     # CHAT TEMPLATE
#     # --------------------------------------------------------

#     text = processor.apply_chat_template(

#         messages,

#         tokenize=False,

#         add_generation_prompt=True

#     )


#     # --------------------------------------------------------
#     # PROCESS INPUT
#     # --------------------------------------------------------

#     inputs = processor(

#         text=[text],

#         padding=True,

#         return_tensors="pt"

#     )


#     # --------------------------------------------------------
#     # MOVE INPUTS
#     # --------------------------------------------------------

#     if torch.cuda.is_available():

#         inputs = {

#             key: value.to("cuda")

#             if hasattr(value, "to")

#             else value

#             for key, value in inputs.items()

#         }

#     else:

#         inputs = {

#             key: value.to("cpu")

#             if hasattr(value, "to")

#             else value

#             for key, value in inputs.items()

#         }


#     # --------------------------------------------------------
#     # GENERATE
#     # --------------------------------------------------------

#     generation_start = time.time()

#     with torch.no_grad():

#         generated_ids = model.generate(

#             **inputs,

#             max_new_tokens=350,

#             do_sample=False,

#             repetition_penalty=1.08

#         )


#     generation_time = time.time() - generation_start


#     # --------------------------------------------------------
#     # REMOVE INPUT TOKENS
#     # --------------------------------------------------------

#     input_ids = inputs["input_ids"]

#     trimmed_ids = [

#         output_ids[len(input_ids[index]):]

#         for index, output_ids
#         in enumerate(generated_ids)

#     ]


#     # --------------------------------------------------------
#     # DECODE
#     # --------------------------------------------------------

#     output_text = processor.batch_decode(

#         trimmed_ids,

#         skip_special_tokens=True,

#         clean_up_tokenization_spaces=True

#     )


#     # --------------------------------------------------------
#     # CHECK OUTPUT
#     # --------------------------------------------------------

#     if not output_text:

#         return (
#             "The patient provided a concern, but "
#             "the AI summary could not be generated."
#         )


#     summary = output_text[0].strip()


#     if not summary:

#         return (
#             "The patient provided a concern, but "
#             "the AI summary could not be generated."
#         )


#     # --------------------------------------------------------
#     # TERMINAL DEBUG
#     # --------------------------------------------------------

#     print()
#     print("========================================")
#     print("Qwen Summary Generated")
#     print("========================================")
#     print(
#         f"Model loading time: "
#         f"{model_load_time:.2f} seconds"
#     )
#     print(
#         f"Generation time: "
#         f"{generation_time:.2f} seconds"
#     )
#     print("----------------------------------------")
#     print(summary)
#     print("========================================")
#     print()

#     return summary


# # ============================================================
# # HEADER
# # ============================================================

# st.title("📅 HopeLeaf Appointments")

# st.write(
#     "Book an appointment with a registered HopeLeaf doctor."
# )

# st.divider()


# # ============================================================
# # AI STATUS
# # ============================================================

# with st.expander(
#     "AI Summary Engine",
#     expanded=False
# ):

#     st.write(
#         f"**Model:** {MODEL_NAME}"
#     )

#     st.write(
#         f"**Device:** {DEVICE.upper()}"
#     )

#     st.write(
#         "**Processing:** Local Qwen AI"
#     )

#     if torch.cuda.is_available():

#         st.success(
#             "Qwen is configured to run on the NVIDIA GPU."
#         )

#         try:

#             st.write(
#                 f"**GPU:** "
#                 f"{torch.cuda.get_device_name(0)}"
#             )

#         except Exception:

#             pass

#     else:

#         st.warning(
#             "CUDA is not available. Qwen will run on CPU."
#         )


# # ============================================================
# # GET DOCTORS
# # ============================================================

# doctors = list(

#     users_collection.find(

#         {
#             "role": "doctor"
#         },

#         {
#             "_id": 1,
#             "name": 1,
#             "email": 1
#         }

#     )

# )


# if not doctors:

#     st.warning(
#         "No doctors are registered yet."
#     )

#     st.stop()


# doctor_options = {

#     f"{doctor['name']} ({doctor['email']})":
#         doctor

#     for doctor in doctors

# }


# # ============================================================
# # BOOKING FORM
# # ============================================================

# st.subheader(
#     "Book an Appointment"
# )


# selected_doctor_label = st.selectbox(

#     "Select Doctor",

#     list(
#         doctor_options.keys()
#     )

# )


# selected_doctor = doctor_options[
#     selected_doctor_label
# ]


# # ============================================================
# # PATIENT INFORMATION
# # ============================================================

# st.markdown(
#     "### Patient Information"
# )


# patient_email = st.text_input(

#     "Patient Email",

#     placeholder="patient@hopeleaf.com"

# )


# # ============================================================
# # APPOINTMENT DETAILS
# # ============================================================

# st.markdown(
#     "### Appointment Details"
# )


# appointment_date = st.date_input(

#     "Appointment Date",

#     min_value=date.today()

# )


# appointment_time = st.time_input(

#     "Appointment Time"

# )


# reason = st.text_area(

#     "What are you experiencing?",

#     placeholder=(
#         "Describe what you are feeling in your own words. "
#         "For example: I have been feeling an ache in my "
#         "abdomen for two days and it gets worse after eating..."
#     ),

#     height=180

# )


# st.caption(

#     "Your description will be analyzed by HopeLeaf's "
#     "local Qwen AI and summarized for the doctor."

# )


# # ============================================================
# # CONFIRM APPOINTMENT
# # ============================================================

# if st.button(

#     "Confirm Appointment",

#     type="primary",

#     use_container_width=True

# ):

#     # ========================================================
#     # VALIDATE PATIENT EMAIL
#     # ========================================================

#     if not patient_email.strip():

#         st.error(
#             "Please enter your patient email."
#         )

#         st.stop()


#     # ========================================================
#     # FIND PATIENT
#     # ========================================================

#     patient = users_collection.find_one(

#         {
#             "email": patient_email.strip().lower(),

#             "role": "patient"
#         }

#     )


#     if not patient:

#         st.error(
#             "No patient account was found with this email."
#         )

#         st.info(

#             "Please enter the same email address "
#             "used for your HopeLeaf patient account."

#         )

#         st.stop()


#     # ========================================================
#     # VALIDATE REASON
#     # ========================================================

#     if not reason.strip():

#         st.error(

#             "Please describe what you are experiencing "
#             "before booking the appointment."

#         )

#         st.stop()


#     # ========================================================
#     # APPOINTMENT DATETIME
#     # ========================================================

#     appointment_datetime = datetime.combine(

#         appointment_date,

#         appointment_time

#     )


#     # ========================================================
#     # QWEN SUMMARY
#     # ========================================================

#     with st.spinner(

#         "Qwen is analyzing the patient's description..."

#     ):

#         try:

#             qwen_start = time.time()

#             ai_summary = generate_patient_summary(
#                 reason
#             )

#             qwen_total_time = (
#                 time.time() - qwen_start
#             )

#         except Exception as error:

#             st.error(
#                 "Qwen could not generate the patient summary."
#             )

#             st.exception(error)

#             st.stop()


#     # ========================================================
#     # SAVE APPOINTMENT
#     # ========================================================

#     appointment = {

#         # ----------------------------------------------------
#         # Patient
#         # ----------------------------------------------------

#         "patient_id": patient["_id"],

#         "patient_name": patient["name"],

#         "patient_email": patient["email"],


#         # ----------------------------------------------------
#         # Doctor
#         # ----------------------------------------------------

#         "doctor_id": selected_doctor["_id"],

#         "doctor_name": selected_doctor["name"],

#         "doctor_email": selected_doctor["email"],


#         # ----------------------------------------------------
#         # Appointment
#         # ----------------------------------------------------

#         "date": appointment_date.isoformat(),

#         "time": appointment_time.strftime("%H:%M"),

#         "appointment_datetime":
#             appointment_datetime,


#         # ----------------------------------------------------
#         # Original patient description
#         # ----------------------------------------------------

#         "reason": reason.strip(),


#         # ----------------------------------------------------
#         # Qwen generated summary
#         # ----------------------------------------------------

#         "ai_summary": ai_summary,


#         # ----------------------------------------------------
#         # Appointment status
#         # ----------------------------------------------------

#         "status": "scheduled",


#         # ----------------------------------------------------
#         # Created timestamp
#         # ----------------------------------------------------

#         "created_at": datetime.utcnow()

#     }


#     # ========================================================
#     # SAVE TO MONGODB
#     # ========================================================

#     try:

#         result = appointments_collection.insert_one(

#             appointment

#         )

#     except Exception as error:

#         st.error(
#             "Could not save the appointment."
#         )

#         st.exception(error)

#         st.stop()


#     # ========================================================
#     # SUCCESS
#     # ========================================================

#     st.success(

#         f"Appointment booked with "
#         f"Dr. {selected_doctor['name']}."

#     )


#     st.divider()


#     # ========================================================
#     # CONFIRMATION
#     # ========================================================

#     st.subheader(
#         "Appointment Confirmed"
#     )


#     col1, col2 = st.columns(2)


#     with col1:

#         st.write("**Patient**")

#         st.write(
#             patient["name"]
#         )

#         st.write("**Doctor**")

#         st.write(
#             f"Dr. {selected_doctor['name']}"
#         )


#     with col2:

#         st.write("**Date**")

#         st.write(

#             appointment_date.strftime(
#                 "%d %B %Y"
#             )

#         )

#         st.write("**Time**")

#         st.write(

#             appointment_time.strftime(
#                 "%H:%M"
#             )

#         )


#     # ========================================================
#     # PATIENT DESCRIPTION
#     # ========================================================

#     st.subheader(
#         "Patient's Description"
#     )


#     st.info(
#         reason.strip()
#     )


#     # ========================================================
#     # AI SUMMARY
#     # ========================================================

#     st.subheader(
#         "AI Patient Summary"
#     )


#     st.caption(
#         "AI-generated assistance for clinical review"
#     )


#     st.markdown(
#         ai_summary
#     )


#     # ========================================================
#     # QWEN PROCESSING INFORMATION
#     # ========================================================

#     with st.expander(
#         "Qwen Processing Information"
#     ):

#         st.write(
#             f"**Model:** {MODEL_NAME}"
#         )

#         st.write(
#             f"**Device:** {DEVICE.upper()}"
#         )

#         st.write(
#             f"**Total processing time:** "
#             f"{qwen_total_time:.2f} seconds"
#         )

#         st.success(
#             "Summary generated locally using Qwen."
#         )


#     # ========================================================
#     # SAFETY NOTICE
#     # ========================================================

#     st.warning(

#         "This summary is generated from the patient's "
#         "own description using a local Qwen model. "
#         "It is not a diagnosis, clinical conclusion, "
#         "or treatment recommendation."

#     )


#     # ========================================================
#     # APPOINTMENT REFERENCE
#     # ========================================================

#     with st.expander(
#         "Appointment Reference"
#     ):

#         st.write(
#             "Appointment ID"
#         )

#         st.code(
#             str(result.inserted_id)
#         )

import streamlit as st
import torch
import time

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from datetime import datetime, date

from transformers import (
    AutoProcessor,
    Qwen2VLForConditionalGeneration
)


# ============================================================
# CONFIG
# ============================================================

MONGODB_URI = "mongodb://127.0.0.1:27017/hopeleaf"

MODEL_NAME = "Qwen/Qwen2-VL-2B-Instruct"


# ============================================================
# DEVICE
# ============================================================

if torch.cuda.is_available():

    DEVICE = "cuda"
    DTYPE = torch.bfloat16

else:

    DEVICE = "cpu"
    DTYPE = torch.float32


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="HopeLeaf Appointments",
    page_icon="📅",
    layout="centered"
)


# ============================================================
# DATABASE
# ============================================================

@st.cache_resource(show_spinner=False)
def get_database():

    client = MongoClient(MONGODB_URI)

    client.admin.command("ping")

    return client["hopeleaf"]


try:

    db = get_database()

    users_collection = db["users"]

    appointments_collection = db["appointments"]

except Exception as error:

    st.error(
        "Could not connect to HopeLeaf database."
    )

    st.code(str(error))

    st.stop()


# ============================================================
# DUPLICATE APPOINTMENT INDEX
# ============================================================
#
# This prevents two identical scheduled appointments from
# being inserted even if two requests arrive at almost the
# same time.
#
# A cancelled appointment does NOT block the patient from
# booking the same slot again.
#
# ============================================================

try:

    appointments_collection.create_index(
        [
            ("patient_id", 1),
            ("doctor_id", 1),
            ("appointment_datetime", 1)
        ],
        unique=True,
        partialFilterExpression={
            "status": "scheduled"
        },
        name="unique_scheduled_appointment"
    )

except Exception as error:

    print(
        "Could not create appointment uniqueness index:",
        error
    )


# ============================================================
# QWEN MODEL
# ============================================================

@st.cache_resource(show_spinner=False)
def load_model():

    start_time = time.time()

    print()
    print("========================================")
    print("HopeLeaf Qwen AI")
    print("========================================")

    print("Model:", MODEL_NAME)

    print(
        "CUDA available:",
        torch.cuda.is_available()
    )


    # ========================================================
    # GPU
    # ========================================================

    if torch.cuda.is_available():

        gpu_name = torch.cuda.get_device_name(0)

        print("GPU:", gpu_name)

        print(
            "Loading Qwen directly onto GPU..."
        )

        try:

            model = (
                Qwen2VLForConditionalGeneration
                .from_pretrained(
                    MODEL_NAME,
                    torch_dtype=DTYPE
                )
            )

            model = model.to("cuda")

            processor = AutoProcessor.from_pretrained(
                MODEL_NAME
            )

        except Exception as error:

            print(
                "Qwen GPU loading failed."
            )

            print(error)

            raise error


    # ========================================================
    # CPU
    # ========================================================

    else:

        print(
            "CUDA is not available."
        )

        print(
            "Loading Qwen on CPU..."
        )

        try:

            model = (
                Qwen2VLForConditionalGeneration
                .from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float32
                )
            )

            model = model.to("cpu")

            processor = AutoProcessor.from_pretrained(
                MODEL_NAME
            )

        except Exception as error:

            print(
                "Qwen CPU loading failed."
            )

            print(error)

            raise error


    # ========================================================
    # EVALUATION MODE
    # ========================================================

    model.eval()

    load_time = (
        time.time()
        - start_time
    )

    print(
        "----------------------------------------"
    )

    print(
        "Qwen loaded successfully."
    )

    print(
        f"Model loading time: "
        f"{load_time:.2f} seconds"
    )

    print(
        "Running device:",
        DEVICE.upper()
    )

    print(
        "========================================"
    )

    print()

    return (
        model,
        processor,
        load_time
    )


# ============================================================
# GENERATE PATIENT SUMMARY
# ============================================================

def generate_patient_summary(patient_reason):

    # ========================================================
    # EMPTY DESCRIPTION
    # ========================================================

    if not patient_reason:

        return (
            "The patient did not provide a description "
            "of their concern."
        )

    patient_reason = patient_reason.strip()

    if not patient_reason:

        return (
            "The patient did not provide a description "
            "of their concern."
        )


    # ========================================================
    # LOAD QWEN
    # ========================================================

    model, processor, model_load_time = load_model()


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """

You are HopeLeaf's clinical documentation assistant.

Your task is to convert a patient's own description
into a clear, concise, natural, professional
patient-reported summary for a doctor.

This is documentation assistance only.

STRICT RULES:

1. ONLY use information explicitly provided by the patient.

2. NEVER invent symptoms.

3. NEVER invent severity.

4. NEVER invent duration.

5. NEVER invent onset.

6. NEVER invent location.

7. NEVER invent frequency.

8. NEVER invent triggers.

9. NEVER invent relieving factors.

10. NEVER invent worsening factors.

11. NEVER invent associated symptoms.

12. NEVER invent medical history.

13. NEVER invent medications.

14. NEVER invent allergies.

15. NEVER diagnose a disease.

16. NEVER provide treatment advice.

17. NEVER recommend medication.

18. NEVER make a clinical conclusion.

19. NEVER assume information that was not stated.

20. NEVER exaggerate symptoms.

21. NEVER minimize symptoms.

22. Preserve the patient's meaning.

23. If the patient gives a numeric severity,
    preserve the exact number.

24. If the patient says "mild", "moderate", "severe",
    "very severe", "unbearable", etc., preserve
    those words exactly in meaning.

25. Never convert a verbal severity into a number.

26. Never convert a number into a different severity.

27. If information is missing, do not invent it.


SUMMARY:

Write a natural clinical documentation summary.

Start with:

"The patient reports..."

Include information ONLY when it was provided:

- main complaint
- symptoms
- location
- type or character of symptoms
- onset
- duration
- frequency
- severity
- numeric severity
- associated symptoms
- triggers
- relieving factors
- worsening factors
- other relevant information


The summary should normally be 1-3 sentences.

Do not turn the summary into a checklist.

Do not repeat the patient's sentence unnecessarily.


POINTS TO CLARIFY:

After the summary, create:

Points to clarify

Ask 3-5 concise questions about important information
that is genuinely missing.

Prioritize:

1. Location

2. Onset and duration

3. Severity

4. Frequency or pattern

5. Factors that make symptoms better or worse

6. Important associated symptoms


BUT:

Do NOT ask about information that the patient
already clearly provided.

For example:

Patient:

"I have chest pain for two days."

Do NOT ask:

"When did the pain start?"

Do NOT ask:

"How long have you had the pain?"

Instead ask about information that is missing, such as:

"Where exactly is the chest pain located?"

"How severe is the pain?"

"Does anything make the pain better or worse?"

If location is already provided,
do not ask about location.

If duration is already provided,
do not ask about duration.

If severity is already provided,
do not ask about severity.

If a symptom has no obvious useful clarification,
do not create an unnecessary generic question.

Questions should be relevant to the patient's
specific complaint.

Do not generate generic questions simply to fill space.

Do not provide a diagnosis.

Do not provide treatment.

Do not provide medical advice.

Return plain text only.

Use exactly this structure:

The patient reports [summary].

Points to clarify

1. [question]

2. [question]

3. [question]

"""


    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""

Patient's own description:

{patient_reason}

Carefully analyze only what the patient actually said.

Create a faithful patient-reported clinical summary.

Then provide only the most important missing
information that the doctor may want to clarify.

Do not invent anything.

"""


    # ========================================================
    # CHAT MESSAGES
    # ========================================================

    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": user_prompt
        }

    ]


    # ========================================================
    # CHAT TEMPLATE
    # ========================================================

    text = processor.apply_chat_template(

        messages,

        tokenize=False,

        add_generation_prompt=True

    )


    # ========================================================
    # PROCESS INPUT
    # ========================================================

    inputs = processor(

        text=[text],

        padding=True,

        return_tensors="pt"

    )


    # ========================================================
    # MOVE INPUTS
    # ========================================================

    if torch.cuda.is_available():

        inputs = {

            key: value.to("cuda")
            if hasattr(value, "to")
            else value

            for key, value in inputs.items()

        }

    else:

        inputs = {

            key: value.to("cpu")
            if hasattr(value, "to")
            else value

            for key, value in inputs.items()

        }


    # ========================================================
    # GENERATE
    # ========================================================

    generation_start = time.time()

    with torch.no_grad():

        generated_ids = model.generate(

            **inputs,

            max_new_tokens=350,

            do_sample=False,

            repetition_penalty=1.08

        )

    generation_time = (
        time.time()
        - generation_start
    )


    # ========================================================
    # REMOVE INPUT TOKENS
    # ========================================================

    input_ids = inputs["input_ids"]

    trimmed_ids = [

        output_ids[
            len(input_ids[index]):
        ]

        for index, output_ids
        in enumerate(generated_ids)

    ]


    # ========================================================
    # DECODE
    # ========================================================

    output_text = processor.batch_decode(

        trimmed_ids,

        skip_special_tokens=True,

        clean_up_tokenization_spaces=True

    )


    # ========================================================
    # CHECK OUTPUT
    # ========================================================

    if not output_text:

        return (
            "The patient provided a concern, but "
            "the AI summary could not be generated."
        )

    summary = output_text[0].strip()

    if not summary:

        return (
            "The patient provided a concern, but "
            "the AI summary could not be generated."
        )


    # ========================================================
    # TERMINAL DEBUG
    # ========================================================

    print()

    print(
        "========================================"
    )

    print(
        "Qwen Summary Generated"
    )

    print(
        "========================================"
    )

    print(
        f"Model loading time: "
        f"{model_load_time:.2f} seconds"
    )

    print(
        f"Generation time: "
        f"{generation_time:.2f} seconds"
    )

    print(
        "----------------------------------------"
    )

    print(summary)

    print(
        "========================================"
    )

    print()

    return summary


# ============================================================
# RECOMMEND SPECIALIST
# ============================================================

def recommend_specialist(patient_reason):

    # ========================================================
    # EMPTY DESCRIPTION
    # ========================================================

    if not patient_reason:

        return (
            "Recommended Specialist: General Physician\n\n"
            "Reason:\n"
            "No patient description was provided."
        )

    patient_reason = patient_reason.strip()

    if not patient_reason:

        return (
            "Recommended Specialist: General Physician\n\n"
            "Reason:\n"
            "No patient description was provided."
        )


    # ========================================================
    # LOAD QWEN
    # ========================================================

    model, processor, model_load_time = load_model()


    # ========================================================
    # SPECIALIST PROMPT
    # ========================================================

    system_prompt = """

You are HopeLeaf's healthcare navigation assistant.

Your task is ONLY to recommend an appropriate
medical specialty based on the symptoms or concern
explicitly described by the patient.

IMPORTANT SAFETY RULES:

1. Do NOT diagnose the patient.

2. Do NOT identify a disease.

3. Do NOT provide treatment.

4. Do NOT recommend medication.

5. Do NOT invent symptoms.

6. Use ONLY information explicitly provided
   by the patient.

7. If the information is insufficient,
   recommend General Physician.

8. The recommendation is only a navigation
   suggestion.

9. Do not claim that a specialist is
   definitely required.


Choose ONLY ONE specialty from this list:

- General Physician
- Cardiologist
- Neurologist
- Gastroenterologist
- Pulmonologist
- Dermatologist
- Orthopedic Specialist
- Urologist
- Gynecologist
- ENT Specialist
- Ophthalmologist
- Endocrinologist
- Psychiatrist
- Dentist


Return exactly this format:

Recommended Specialist: [specialty]

Reason:
[One short sentence explaining why this specialty
may be relevant based ONLY on the patient's description.]

Do not diagnose.

Do not provide treatment.

Do not invent information.

"""


    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""

Patient's description:

{patient_reason}

Recommend the single most appropriate specialist
from the allowed list.

If the description does not provide enough information,
choose General Physician.

Do not diagnose.
Do not provide treatment.
Do not invent information.

"""


    # ========================================================
    # CHAT
    # ========================================================

    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": user_prompt
        }

    ]


    text = processor.apply_chat_template(

        messages,

        tokenize=False,

        add_generation_prompt=True

    )


    # ========================================================
    # PROCESS
    # ========================================================

    inputs = processor(

        text=[text],

        padding=True,

        return_tensors="pt"

    )


    # ========================================================
    # DEVICE
    # ========================================================

    if torch.cuda.is_available():

        inputs = {

            key: value.to("cuda")
            if hasattr(value, "to")
            else value

            for key, value in inputs.items()

        }

    else:

        inputs = {

            key: value.to("cpu")
            if hasattr(value, "to")
            else value

            for key, value in inputs.items()

        }


    # ========================================================
    # GENERATE
    # ========================================================

    with torch.no_grad():

        generated_ids = model.generate(

            **inputs,

            max_new_tokens=120,

            do_sample=False,

            repetition_penalty=1.08

        )


    # ========================================================
    # REMOVE INPUT TOKENS
    # ========================================================

    input_ids = inputs["input_ids"]

    trimmed_ids = [

        output_ids[
            len(input_ids[index]):
        ]

        for index, output_ids
        in enumerate(generated_ids)

    ]


    # ========================================================
    # DECODE
    # ========================================================

    output_text = processor.batch_decode(

        trimmed_ids,

        skip_special_tokens=True,

        clean_up_tokenization_spaces=True

    )


    # ========================================================
    # FALLBACK
    # ========================================================

    if not output_text:

        return (
            "Recommended Specialist: General Physician\n\n"
            "Reason:\n"
            "A general physician can initially review "
            "the patient's concern."
        )


    recommendation = output_text[0].strip()


    if not recommendation:

        return (
            "Recommended Specialist: General Physician\n\n"
            "Reason:\n"
            "A general physician can initially review "
            "the patient's concern."
        )


    print()

    print(
        "========================================"
    )

    print(
        "Qwen Specialist Recommendation"
    )

    print(
        "========================================"
    )

    print(recommendation)

    print(
        "========================================"
    )

    print()

    return recommendation


# ============================================================
# HEADER
# ============================================================

st.title(
    "📅 HopeLeaf Appointments"
)

st.write(
    "Book an appointment with a registered HopeLeaf doctor."
)

st.divider()


# ============================================================
# AI STATUS
# ============================================================

with st.expander(
    "AI Summary Engine",
    expanded=False
):

    st.write(
        f"**Model:** {MODEL_NAME}"
    )

    st.write(
        f"**Device:** {DEVICE.upper()}"
    )

    st.write(
        "**Processing:** Local Qwen AI"
    )

    if torch.cuda.is_available():

        st.success(
            "Qwen is configured to run on the NVIDIA GPU."
        )

        try:

            st.write(
                f"**GPU:** "
                f"{torch.cuda.get_device_name(0)}"
            )

        except Exception:

            pass

    else:

        st.warning(
            "CUDA is not available. Qwen will run on CPU."
        )


# ============================================================
# GET DOCTORS
# ============================================================

doctors = list(

    users_collection.find(

        {
            "role": "doctor"
        },

        {
            "_id": 1,
            "name": 1,
            "email": 1
        }

    )

)


if not doctors:

    st.warning(
        "No doctors are registered yet."
    )

    st.stop()


# ============================================================
# DOCTOR OPTIONS
# ============================================================

doctor_options = {

    f"{doctor['name']} ({doctor['email']})":
        doctor

    for doctor in doctors

}


# ============================================================
# BOOKING FORM
# ============================================================

st.subheader(
    "Book an Appointment"
)


selected_doctor_label = st.selectbox(

    "Select Doctor",

    list(
        doctor_options.keys()
    )

)


selected_doctor = doctor_options[
    selected_doctor_label
]


# ============================================================
# PATIENT INFORMATION
# ============================================================

st.markdown(
    "### Patient Information"
)


patient_email = st.text_input(

    "Patient Email",

    placeholder="patient@hopeleaf.com"

)


# ============================================================
# APPOINTMENT DETAILS
# ============================================================

st.markdown(
    "### Appointment Details"
)


appointment_date = st.date_input(

    "Appointment Date",

    min_value=date.today()

)


appointment_time = st.time_input(

    "Appointment Time"

)


reason = st.text_area(

    "What are you experiencing?",

    placeholder=(
        "Describe what you are feeling in your own words. "
        "For example: I have been feeling an ache in my "
        "abdomen for two days and it gets worse after eating..."
    ),

    height=180

)


st.caption(

    "Your description will be analyzed by HopeLeaf's "
    "local Qwen AI and summarized for the doctor."

)


# ============================================================
# CONFIRM APPOINTMENT
# ============================================================

if st.button(

    "Confirm Appointment",

    type="primary",

    use_container_width=True

):

    # ========================================================
    # VALIDATE EMAIL
    # ========================================================

    if not patient_email.strip():

        st.error(
            "Please enter your patient email."
        )

        st.stop()


    # ========================================================
    # FIND PATIENT
    # ========================================================

    patient = users_collection.find_one(

        {
            "email": patient_email.strip().lower(),
            "role": "patient"
        }

    )


    if not patient:

        st.error(
            "No patient account was found with this email."
        )

        st.info(

            "Please enter the same email address "
            "used for your HopeLeaf patient account."

        )

        st.stop()


    # ========================================================
    # VALIDATE REASON
    # ========================================================

    if not reason.strip():

        st.error(

            "Please describe what you are experiencing "
            "before booking the appointment."

        )

        st.stop()


    # ========================================================
    # APPOINTMENT DATETIME
    # ========================================================

    appointment_datetime = datetime.combine(

        appointment_date,

        appointment_time

    )


    # ========================================================
    # DUPLICATE APPOINTMENT CHECK
    # ========================================================
    #
    # This check happens BEFORE Qwen.
    #
    # If the exact same patient already has a scheduled
    # appointment with the same doctor at the same time,
    # we stop immediately.
    #
    # ========================================================

    existing_appointment = (
        appointments_collection.find_one(
            {
                "patient_id": patient["_id"],

                "doctor_id": selected_doctor["_id"],

                "appointment_datetime":
                    appointment_datetime,

                "status": "scheduled"
            }
        )
    )


    if existing_appointment:

        st.error(
            "Duplicate appointment detected."
        )

        st.warning(

            "You already have a scheduled appointment "
            "with this doctor at this date and time."

        )

        st.info(

            f"Doctor: Dr. {selected_doctor['name']}\n\n"
            f"Date: "
            f"{appointment_date.strftime('%d %B %Y')}\n\n"
            f"Time: "
            f"{appointment_time.strftime('%H:%M')}"

        )

        st.stop()


    # ========================================================
    # SPECIALIST RECOMMENDATION
    # ========================================================

    with st.spinner(

        "HopeLeaf is determining a suitable specialist..."

    ):

        try:

            recommendation_start = time.time()

            specialist_recommendation = (
                recommend_specialist(reason)
            )

            recommendation_total_time = (
                time.time()
                - recommendation_start
            )

        except Exception as error:

            print(
                "Specialist recommendation failed:",
                error
            )

            specialist_recommendation = (

                "Recommended Specialist: "
                "General Physician\n\n"

                "Reason:\n"

                "A general physician can initially "
                "review the patient's concern."

            )

            recommendation_total_time = 0


    # ========================================================
    # DISPLAY SPECIALIST RECOMMENDATION
    # ========================================================

    st.divider()

    st.subheader(
        "Recommended Specialist"
    )

    st.info(
        specialist_recommendation
    )

    st.caption(

        "This is a healthcare navigation recommendation "
        "based only on the information you provided. "
        "It is not a diagnosis, clinical conclusion, "
        "or treatment recommendation."

    )


    # ========================================================
    # QWEN PATIENT SUMMARY
    # ========================================================

    with st.spinner(

        "Qwen is analyzing the patient's description..."

    ):

        try:

            qwen_start = time.time()

            ai_summary = generate_patient_summary(
                reason
            )

            qwen_total_time = (
                time.time()
                - qwen_start
            )

        except Exception as error:

            st.error(
                "Qwen could not generate the patient summary."
            )

            st.exception(error)

            st.stop()


    # ========================================================
    # APPOINTMENT DOCUMENT
    # ========================================================

    appointment = {

        # ----------------------------------------------------
        # Patient
        # ----------------------------------------------------

        "patient_id":
            patient["_id"],

        "patient_name":
            patient["name"],

        "patient_email":
            patient["email"],


        # ----------------------------------------------------
        # Doctor
        # ----------------------------------------------------

        "doctor_id":
            selected_doctor["_id"],

        "doctor_name":
            selected_doctor["name"],

        "doctor_email":
            selected_doctor["email"],


        # ----------------------------------------------------
        # Appointment
        # ----------------------------------------------------

        "date":
            appointment_date.isoformat(),

        "time":
            appointment_time.strftime("%H:%M"),

        "appointment_datetime":
            appointment_datetime,


        # ----------------------------------------------------
        # Original patient description
        # ----------------------------------------------------

        "reason":
            reason.strip(),


        # ----------------------------------------------------
        # Qwen generated summary
        # ----------------------------------------------------

        "ai_summary":
            ai_summary,


        # ----------------------------------------------------
        # Specialist recommendation
        # ----------------------------------------------------

        "recommended_specialist":
            specialist_recommendation,


        # ----------------------------------------------------
        # Appointment status
        # ----------------------------------------------------

        "status":
            "scheduled",


        # ----------------------------------------------------
        # Created timestamp
        # ----------------------------------------------------

        "created_at":
            datetime.utcnow()

    }


    # ========================================================
    # SAVE TO MONGODB
    # ========================================================

    try:

        result = (
            appointments_collection.insert_one(
                appointment
            )
        )

    except DuplicateKeyError:

        # ----------------------------------------------------
        # This catches the race condition where another
        # request inserted the exact same appointment between
        # our find_one() check and insert_one().
        # ----------------------------------------------------

        st.error(
            "This appointment was already booked."
        )

        st.warning(

            "Another appointment with the same patient, "
            "doctor, date and time already exists."

        )

        st.stop()

    except Exception as error:

        st.error(
            "Could not save the appointment."
        )

        st.exception(error)

        st.stop()


    # ========================================================
    # SUCCESS
    # ========================================================

    st.success(

        f"Appointment booked with "
        f"Dr. {selected_doctor['name']}."

    )


    st.divider()


    # ========================================================
    # CONFIRMATION
    # ========================================================

    st.subheader(
        "Appointment Confirmed"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**Patient**"
        )

        st.write(
            patient["name"]
        )

        st.write(
            "**Doctor**"
        )

        st.write(

            f"Dr. {selected_doctor['name']}"

        )


    with col2:

        st.write(
            "**Date**"
        )

        st.write(

            appointment_date.strftime(
                "%d %B %Y"
            )

        )

        st.write(
            "**Time**"
        )

        st.write(

            appointment_time.strftime(
                "%H:%M"
            )

        )


    # ========================================================
    # SPECIALIST RECOMMENDATION
    # ========================================================

    st.subheader(
        "Recommended Specialist"
    )

    st.info(
        specialist_recommendation
    )

    st.caption(

        "This recommendation is for healthcare navigation "
        "only. It does not diagnose a medical condition."

    )


    # ========================================================
    # PATIENT DESCRIPTION
    # ========================================================

    st.subheader(
        "Patient's Description"
    )

    st.info(
        reason.strip()
    )


    # ========================================================
    # AI SUMMARY
    # ========================================================

    st.subheader(
        "AI Patient Summary"
    )

    st.caption(
        "AI-generated assistance for clinical review"
    )

    st.markdown(
        ai_summary
    )


    # ========================================================
    # QWEN PROCESSING INFORMATION
    # ========================================================

    with st.expander(
        "Qwen Processing Information"
    ):

        st.write(
            f"**Model:** {MODEL_NAME}"
        )

        st.write(
            f"**Device:** {DEVICE.upper()}"
        )

        st.write(

            f"**Summary processing time:** "
            f"{qwen_total_time:.2f} seconds"

        )

        st.write(

            f"**Specialist recommendation time:** "
            f"{recommendation_total_time:.2f} seconds"

        )

        st.success(
            "Summary generated locally using Qwen."
        )


    # ========================================================
    # SAFETY NOTICE
    # ========================================================

    st.warning(

        "The patient summary and specialist recommendation "
        "are generated from the patient's own description "
        "using a local Qwen model. They are not a diagnosis, "
        "clinical conclusion, or treatment recommendation."

    )


    # ========================================================
    # APPOINTMENT REFERENCE
    # ========================================================

    with st.expander(
        "Appointment Reference"
    ):

        st.write(
            "Appointment ID"
        )

        st.code(
            str(result.inserted_id)
        )