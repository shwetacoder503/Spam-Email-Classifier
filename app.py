import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import tempfile
import os
import time
from datetime import datetime

from src.pipeline.prediction_pipeline import PredictionPipeline

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="SpamGuard AI | Intelligent Email Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SESSION STATE (for animated / running stats)
# =========================================================
if "total_scanned" not in st.session_state:
    st.session_state.total_scanned = 0
if "spam_detected" not in st.session_state:
    st.session_state.spam_detected = 0
if "ham_detected" not in st.session_state:
    st.session_state.ham_detected = 0
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "batch_df" not in st.session_state:
    st.session_state.batch_df = None

# =========================================================
# CUSTOM CSS — DARK GLASSMORPHIC SAAS THEME
# =========================================================
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 15% 10%, #1a1f3c 0%, #0b0e1a 45%, #05070d 100%);
    color: #E5E7EB;
}

/* ---------------- SIDEBAR ---------------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #11142b 0%, #0a0c1a 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}
.sidebar-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(90deg, #7C3AED, #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2px;
}
.sidebar-sub {
    color: #6B7280;
    font-size: 13px;
    margin-bottom: 25px;
}
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px 16px !important;
    margin-bottom: 8px;
    width: 100%;
    transition: all 0.25s ease;
    cursor: pointer;
}
div[role="radiogroup"] label:hover {
    background: rgba(124,58,237,0.15);
    border-color: rgba(124,58,237,0.5);
}
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
    display:none;
}

/* ---------------- HERO ---------------- */
.hero {
    padding: 45px 40px;
    border-radius: 24px;
    background: linear-gradient(120deg, rgba(124,58,237,0.25), rgba(34,211,238,0.15));
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(124,58,237,0.45), transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 44px;
    font-weight: 700;
    color: #F9FAFB;
    margin-bottom: 6px;
}
.hero-gradient-word {
    background: linear-gradient(90deg, #A78BFA, #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-sub {
    color: #9CA3AF;
    font-size: 17px;
    max-width: 620px;
    line-height: 1.5;
}
.hero-badge {
    display:inline-block;
    background: rgba(34,211,238,0.12);
    color:#22D3EE;
    border:1px solid rgba(34,211,238,0.35);
    padding:5px 14px;
    border-radius:999px;
    font-size:12px;
    font-weight:600;
    letter-spacing:0.5px;
    margin-bottom:16px;
}

/* ---------------- GLASS CARD ---------------- */
.glass-card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 26px;
    margin-bottom: 22px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 600;
    color: #F3F4F6;
    margin-bottom: 4px;
}
.section-caption {
    color: #6B7280;
    font-size: 14px;
    margin-bottom: 18px;
}

/* ---------------- METRIC CARDS ---------------- */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 20px;
    text-align:center;
    transition: transform 0.25s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(124,58,237,0.5);
}
.metric-value {
    font-family:'Space Grotesk', sans-serif;
    font-size: 34px;
    font-weight: 700;
    color: #F9FAFB;
}
.metric-label {
    color:#9CA3AF;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* ---------------- RESULT CARDS ---------------- */
.result-spam {
    background: linear-gradient(135deg, rgba(239,68,68,0.18), rgba(239,68,68,0.05));
    border: 1px solid rgba(239,68,68,0.45);
    border-radius: 20px;
    padding: 28px;
    text-align:center;
    margin-bottom: 20px;
}
.result-ham {
    background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(16,185,129,0.05));
    border: 1px solid rgba(16,185,129,0.45);
    border-radius: 20px;
    padding: 28px;
    text-align:center;
    margin-bottom: 20px;
}
.result-label {
    font-family:'Space Grotesk', sans-serif;
    font-size: 30px;
    font-weight: 700;
}
.result-spam .result-label { color:#F87171; }
.result-ham .result-label { color:#34D399; }
.result-icon { font-size: 46px; margin-bottom: 6px; }

/* ---------------- REASON CHIPS ---------------- */
.reason-chip {
    display:inline-block;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.35);
    color:#C4B5FD;
    padding: 8px 14px;
    border-radius: 10px;
    margin: 5px 6px 5px 0;
    font-size: 13.5px;
}

/* ---------------- BUTTONS ---------------- */
.stButton>button, .stDownloadButton>button {
    width:100%;
    border-radius: 12px;
    height: 52px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    background: linear-gradient(90deg, #7C3AED, #22D3EE);
    color: white;
    transition: all 0.25s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    filter: brightness(1.12);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(124,58,237,0.35);
}

/* ---------------- TEXT AREA / UPLOAD ---------------- */
textarea, .stTextArea textarea {
    border-radius: 14px !important;
    background: rgba(255,255,255,0.03) !important;
    color: #E5E7EB !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,0.03);
    border: 1px dashed rgba(124,58,237,0.5);
    border-radius: 16px;
}

/* ---------------- DATAFRAME ---------------- */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* ---------------- FOOTER ---------------- */
.footer {
    text-align:center;
    color:#4B5563;
    margin-top: 50px;
    padding: 20px 0 10px 0;
    font-size: 13px;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.footer span {
    color:#A78BFA;
    font-weight:600;
}

/* progress bar recolor */
.stProgress > div > div > div > div {
    background-image: linear-gradient(90deg, #7C3AED, #22D3EE);
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD ML PIPELINE
# =========================================================
@st.cache_resource
def get_pipeline():
    return PredictionPipeline(load_models=True)

try:
    pipeline = get_pipeline()
    model_status = "🟢 Online"
except Exception as e:
    st.error(f"Error loading models: {str(e)}")
    st.stop()


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def render_confidence_gauge(confidence, prediction):
    color = "#F87171" if prediction == "Spam" else "#34D399"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(confidence),
        number={'suffix': "%", 'font': {'size': 40, 'color': '#F9FAFB'}},
        title={'text': "Model Confidence", 'font': {'size': 16, 'color': '#9CA3AF'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#6B7280', 'tickfont': {'color': '#6B7280'}},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': 'rgba(255,255,255,0.05)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255,255,255,0.03)'},
                {'range': [50, 80], 'color': 'rgba(255,255,255,0.05)'},
                {'range': [80, 100], 'color': 'rgba(255,255,255,0.07)'},
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#E5E7EB'},
        height=280,
        margin=dict(t=50, b=10, l=30, r=30)
    )
    return fig


def render_probability_bar(confidence, prediction):
    if prediction == "Spam":
        spam_p, ham_p = float(confidence), 100 - float(confidence)
    else:
        ham_p, spam_p = float(confidence), 100 - float(confidence)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[spam_p], y=["Spam"], orientation='h',
        marker=dict(color="#F87171"), text=[f"{spam_p:.1f}%"], textposition='inside'
    ))
    fig.add_trace(go.Bar(
        x=[ham_p], y=["Ham"], orientation='h',
        marker=dict(color="#34D399"), text=[f"{ham_p:.1f}%"], textposition='inside'
    ))
    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#E5E7EB'},
        height=160,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
        xaxis=dict(showgrid=False, range=[0, 100], visible=False),
        yaxis=dict(showgrid=False)
    )
    return fig


def render_batch_pie(spam_count, ham_count):
    fig = go.Figure(data=[go.Pie(
        labels=["Spam", "Ham"],
        values=[spam_count, ham_count],
        hole=0.55,
        marker=dict(colors=["#F87171", "#34D399"]),
        textfont=dict(color="#0b0e1a", size=14)
    )])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': '#E5E7EB'},
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", y=-0.1)
    )
    return fig


def metric_card(label, value, col):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.markdown("<div class='sidebar-brand'>🛡️ SpamGuard AI</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-sub'>Intelligent Email Threat Detection</div>", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📩 Single Email Scan", "📂 Batch MBOX Processing", "ℹ️ About Model"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown(f"**Model Status:** {model_status}")
    st.markdown("**Engine:** TF-IDF + SVM")
    st.markdown(f"**Session Scans:** {st.session_state.total_scanned}")
    st.markdown("---")
    #st.caption("Built for portfolio demonstration • v2.0")


# =========================================================
# HERO SECTION (shown on Dashboard)
# =========================================================
def render_hero():
    st.markdown(f"""
    <div class="hero">
        <div class="hero-badge">⚡ POWERED BY MACHINE LEARNING</div>
        <div class="hero-title">Stop Spam Before It <span class="hero-gradient-word">Reaches You</span></div>
        <div class="hero-sub">
            SpamGuard AI uses a TF-IDF vectorized Support Vector Machine to classify emails
            in real time — analyze single messages or process entire MBOX archives with
            enterprise-grade accuracy.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# PAGE: DASHBOARD
# =========================================================
if page == "🏠 Dashboard":
    render_hero()

    st.markdown("<div class='section-title'>📊 Live Session Statistics</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-caption'>Metrics update automatically as you scan emails.</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    metric_card("Total Scanned", st.session_state.total_scanned, c1)
    metric_card("Spam Detected", st.session_state.spam_detected, c2)
    metric_card("Ham (Safe)", st.session_state.ham_detected, c3)
    spam_rate = (
        round((st.session_state.spam_detected / st.session_state.total_scanned) * 100, 1)
        if st.session_state.total_scanned > 0 else 0
    )
    metric_card("Spam Rate", f"{spam_rate}%", c4)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">📩 Single Email Scan</div>
            <div class="section-caption">Paste any email content and get an instant spam/ham verdict with confidence scoring and reasoning.</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title">📂 Batch MBOX Processing</div>
            <div class="section-caption">Upload a full MBOX archive to classify hundreds of emails at once and export a detailed CSV report.</div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# PAGE: SINGLE EMAIL SCAN
# =========================================================
elif page == "📩 Single Email Scan":

    st.markdown("<div class='hero-title' style='font-size:32px;'>📩 Single Email Scan</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-sub' style='margin-bottom:25px;'>Paste an email body below to analyze it instantly.</div>", unsafe_allow_html=True)

    #st.markdown("<div class='glass-card'></div>", unsafe_allow_html=True)
    email_text = st.text_area(
        "Email Content",
        height=220,
        placeholder="Dear friend, I have a business proposal worth $10,000,000..."
    )
    classify_clicked = st.button("🔍 Classify Email", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if classify_clicked:
        if email_text.strip():
            with st.spinner("🧠 Analyzing email content with AI model..."):
                try:
                    result = pipeline.predict_single_email(email_text)
                    st.session_state.last_result = result

                    prediction = result["prediction"]
                    st.session_state.total_scanned += 1
                    if prediction == "Spam":
                        st.session_state.spam_detected += 1
                    else:
                        st.session_state.ham_detected += 1

                except Exception as e:
                    st.error(f"Error analyzing email: {str(e)}")
                    st.session_state.last_result = None
        else:
            st.warning("⚠️ Please enter some email text before classifying.")

    if st.session_state.last_result:
        result = st.session_state.last_result
        prediction = result["prediction"]
        confidence = result.get("confidence", 0)

        result_class = "result-spam" if prediction == "Spam" else "result-ham"
        icon = "🚨" if prediction == "Spam" else "✅"
        verdict = "SPAM DETECTED" if prediction == "Spam" else "SAFE EMAIL (HAM)"

        st.markdown(f"""
        <div class="{result_class}">
            <div class="result-icon">{icon}</div>
            <div class="result-label">{verdict}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title' style='font-size:18px;'>Confidence Gauge</div>", unsafe_allow_html=True)
            if confidence is not None:
                st.plotly_chart(render_confidence_gauge(confidence, prediction), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title' style='font-size:18px;'>Probability Split</div>", unsafe_allow_html=True)
            if confidence is not None:
                st.plotly_chart(render_probability_bar(confidence, prediction), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title' style='font-size:18px;'>🔎 Why This Prediction?</div>", unsafe_allow_html=True)
        reasons_html = "".join(
            [f"<span class='reason-chip'>✅ {reason}</span>" for reason in result.get("reasons", [])]
        )
        st.markdown(reasons_html if reasons_html else "<i>No specific reasons returned by the model.</i>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Downloadable report
        report_text = (
            f"SpamGuard AI - Email Analysis Report\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'-'*50}\n"
            f"Prediction: {prediction}\n"
            f"Confidence: {confidence:.2f}%\n"
            f"{'-'*50}\n"
            f"Reasons:\n" + "\n".join([f"- {r}" for r in result.get("reasons", [])]) + "\n"
            f"{'-'*50}\n"
            f"Original Email Content:\n{email_text}\n"
        )
        st.download_button(
            label="📥 Download Report (.txt)",
            data=report_text.encode("utf-8"),
            file_name=f"spam_report_{int(time.time())}.txt",
            mime="text/plain"
        )


# =========================================================
# PAGE: BATCH MBOX PROCESSING
# =========================================================
elif page == "📂 Batch MBOX Processing":

    st.markdown("<div class='hero-title' style='font-size:32px;'>📂 Batch MBOX Processing</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-sub' style='margin-bottom:25px;'>Upload an MBOX archive to classify every email inside it in one pass.</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload an MBOX file", type=["mbox", "txt"])
    process_clicked = False
    if uploaded_file is not None:
        process_clicked = st.button("⚙️ Process File", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None and process_clicked:
        with st.spinner("📡 Parsing MBOX archive and classifying emails..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                try:
                    df = pipeline.predict_mbox_file(tmp_path)
                    st.session_state.batch_df = df

                    spam_count = len(df[df["Prediction"] == "Spam"])
                    ham_count = len(df[df["Prediction"] == "Ham"])

                    st.session_state.total_scanned += len(df)
                    st.session_state.spam_detected += spam_count
                    st.session_state.ham_detected += ham_count

                finally:
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.session_state.batch_df = None

    if st.session_state.batch_df is not None:
        df = st.session_state.batch_df
        spam_count = len(df[df["Prediction"] == "Spam"])
        ham_count = len(df[df["Prediction"] == "Ham"])

        c1, c2, c3 = st.columns(3)
        metric_card("Total Emails", len(df), c1)
        metric_card("Spam Emails", spam_count, c2)
        metric_card("Ham Emails", ham_count, c3)

        st.markdown("<br>", unsafe_allow_html=True)

        col_chart, col_table = st.columns([1, 1.4])

        with col_chart:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title' style='font-size:18px;'>Distribution</div>", unsafe_allow_html=True)
            st.plotly_chart(render_batch_pie(spam_count, ham_count), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_table:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title' style='font-size:18px;'>Preview</div>", unsafe_allow_html=True)
            st.dataframe(df[["Time", "Subject", "Prediction"]].head(10), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Full CSV Report",
            data=csv,
            file_name=f"predictions_{int(time.time())}.csv",
            mime="text/csv",
        )


# =========================================================
# PAGE: ABOUT MODEL
# =========================================================
elif page == "ℹ️ About Model":

    st.markdown("<div class='hero-title' style='font-size:32px;'>ℹ️ About the Model</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-sub' style='margin-bottom:25px;'>Technical details behind SpamGuard AI's classification engine.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title" style="font-size:18px;">🧠 Algorithm</div>
            <div class="section-caption">
                Emails are vectorized using <b>TF-IDF (Term Frequency–Inverse Document Frequency)</b>
                and classified using a trained <b>Support Vector Machine (SVM)</b> model,
                optimized for high precision on short-text spam detection.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="glass-card">
            <div class="section-title" style="font-size:18px;">⚙️ Pipeline</div>
            <div class="section-caption">
                The same <code>PredictionPipeline</code> class powers both single-email
                scanning and batch MBOX processing, ensuring consistent predictions
                across the app.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <div class="section-title" style="font-size:18px;">📈 Why Confidence & Reasons Matter</div>
        <div class="section-caption">
            Rather than a black-box output, SpamGuard AI surfaces a confidence percentage
            and human-readable reasons behind each verdict — making the tool explainable
            and trustworthy for real-world use.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div class="footer">
    Built with ❤️ using <span>Streamlit</span> + <span>Plotly</span> ·
    Powered by <span>TF-IDF + SVM</span> · © 2026 SpamGuard AI
</div>
""", unsafe_allow_html=True)
