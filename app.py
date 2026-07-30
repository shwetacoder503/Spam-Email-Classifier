import streamlit as st
import pandas as pd
import tempfile
import os
import time

from src.pipeline.prediction_pipeline import PredictionPipeline

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Spam Email Classifier",
    page_icon="📧",
    layout="centered"
)

# -------------------------------
# Load ML Pipeline
# -------------------------------
@st.cache_resource
def get_pipeline():
    return PredictionPipeline(load_models=True)

try:
    pipeline = get_pipeline()
except Exception as e:
    st.error(f"Error loading models: {str(e)}")
    st.stop()

# -------------------------------
# UI
# -------------------------------
st.title("📧 Spam Email Classifier")
st.markdown("Classify emails as **Spam** or **Ham (Clean)** using Machine Learning.")

tab1, tab2 = st.tabs(["Single Email", "Batch MBOX Processing"])

# ==========================================================
# TAB 1
# ==========================================================
with tab1:

    st.header("Check a Single Email")

    email_text = st.text_area(
        "Paste the email content here:",
        height=200,
        placeholder="Dear friend, I have a business proposal..."
    )

    if st.button("Classify Email", type="primary"):

        if email_text.strip():

            with st.spinner("Analyzing..."):

                try:

                    result = pipeline.predict_single_email(email_text)

                    prediction = result["prediction"]
                    confidence = result.get("confidence", 0)

                    # Prediction
                    if prediction == "Spam":
                        st.error("🚨 This email is **SPAM**")
                    else:
                        st.success("✅ This email is **HAM**")

                    # Confidence
                    if confidence is not None:
                        st.subheader("Confidence")
                        st.progress(float(confidence) / 100)
                        st.info(f"{confidence:.2f}%")

                    # Reasons
                    st.subheader("Why this prediction?")

                    for reason in result["reasons"]:
                        st.write("✅", reason)

                except Exception as e:
                    st.error(f"Error analyzing email: {str(e)}")

        else:
            st.warning("Please enter some email text.")

# ==========================================================
# TAB 2
# ==========================================================
with tab2:

    st.header("Process MBOX File")

    uploaded_file = st.file_uploader(
        "Upload an MBOX file",
        type=["mbox", "txt"]
    )

    if uploaded_file is not None:

        if st.button("Process File"):

            with st.spinner("Processing file..."):

                try:

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    try:

                        df = pipeline.predict_mbox_file(tmp_path)

                        spam_count = len(df[df["Prediction"] == "Spam"])
                        ham_count = len(df[df["Prediction"] == "Ham"])

                        col1, col2 = st.columns(2)

                        col1.metric("Total Emails", len(df))
                        col2.metric("Spam Emails", spam_count)

                        st.subheader("Preview")

                        st.dataframe(
                            df[["Time", "Subject", "Prediction"]].head(10)
                        )

                        csv = df.to_csv(index=False).encode("utf-8")

                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"predictions_{int(time.time())}.csv",
                            mime="text/csv",
                        )

                    finally:

                        if os.path.exists(tmp_path):
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass

                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")