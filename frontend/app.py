import streamlit as st
import requests
import pandas as pd
import json
import os

# Configure page (Must be the first Streamlit command)
st.set_page_config(page_title="Fact Knowledge Layer", layout="wide", initial_sidebar_state="expanded")

API_BASE = "http://localhost:8000/api"

# --- Archival Ledger Custom CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        /* Base Backgrounds & Colors - Paper & Ink Theme */
        .stApp {
            font-family: 'IBM Plex Sans', sans-serif;
        }
        
        /* Main Headers */
        h1, h2, h3 {
            color: #111111 !important;
            font-family: 'Crimson Pro', serif;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        
        /* Ledger Cards (Replacing glassmorphism) */
        .ledger-card {
            background: #ffffff;
            border: 1px solid #d1cbbd; /* Crisp, hard borders */
            padding: 20px;
            margin-bottom: 20px;
            /* NO box-shadow. Strictly flat ledger style. */
        }
        
        /* Relationship Specific Banners */
        .rel-banner {
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.85em;
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            border-radius: 0; /* Square edges */
        }
        .rel-corroboration {
            background: #e8f5e9;
            color: #1b5e20;
            border: 1px solid #1b5e20;
        }
        .rel-contradiction {
            background: #ffebee;
            color: #b71c1c;
            border: 1px solid #b71c1c;
        }
        .rel-contextual {
            background: #fff8e1;
            color: #f57f17;
            border: 1px solid #f57f17;
        }
        .rel-failure {
            background: #f3e5f5;
            color: #4a148c;
            border: 1px solid #4a148c;
        }

        /* Metrics */
        div[data-testid="stMetricValue"] {
            color: #111111;
            font-family: 'Crimson Pro', serif;
            font-size: 3rem !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #5e5c58;
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Sidebar styling */
        .css-1544g2n {
            padding-top: 2rem;
            border-right: 1px solid #d1cbbd;
        }
        
        /* Buttons - Fountain Pen Blue */
        .stButton>button {
            background-color: #1a4b8c;
            color: #ffffff;
            border: none;
            border-radius: 0; /* Sharp corners */
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #113366;
            color: #ffffff;
            box-shadow: none; /* No glow */
        }
        
        /* Fix text colors inside cards */
        .ledger-card p {
            color: #2c2c2c;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .ledger-card strong {
            color: #111111;
        }
        
        /* Two-column layout for relationships */
        .fact-col {
            background: #faf9f6;
            padding: 15px;
            border: 1px solid #d1cbbd;
            flex: 1 1 280px;
            min-width: 280px;
        }
        .fact-col-title {
            color: #5e5c58;
            font-size: 0.75em;
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
            border-bottom: 1px solid #d1cbbd;
            padding-bottom: 5px;
        }
        
        /* Tab Styling overrides to fit theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'IBM Plex Sans', sans-serif;
            color: #5e5c58;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            color: #111111;
            border-bottom-color: #1a4b8c !important;
        }
        
        /* Monogram Logo Style */
        .logo-mark {
            display: inline-block;
            font-family: 'Crimson Pro', serif;
            font-weight: 700;
            font-size: 1.5em;
            color: #f4f1ea;
            background: #111111;
            width: 40px;
            height: 40px;
            text-align: center;
            line-height: 40px;
            border: 2px solid #111111;
            margin-right: 12px;
            vertical-align: middle;
        }
    </style>
""", unsafe_allow_html=True)


# --- State & Data Fetching ---
@st.cache_data(ttl=5)
def fetch_data():
    try:
        facts = requests.get(f"{API_BASE}/facts").json()
        rels = requests.get(f"{API_BASE}/relationships").json()
        return facts, rels
    except:
        return [], []

facts, relationships = fetch_data()

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 30px;">
            <div class="logo-mark">F</div>
            <h2 style="margin:0; font-size: 1.2rem;">Fact Ledger</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Ingest Documents")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if st.button("Process Documents", use_container_width=True):
        if uploaded_files:
            with st.spinner("Extracting factual claims..."):
                for f in uploaded_files:
                    files = {"file": (f.name, f, "application/pdf")}
                    res = requests.post(f"{API_BASE}/upload", files=files)
                    if res.status_code == 200:
                        st.success(f"Processed: {f.name}")
                    else:
                        st.error(f"Failed: {f.name}")
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("<hr style='border: 1px solid #d1cbbd;'>", unsafe_allow_html=True)
    st.subheader("System State")
    if st.button("Sync Ledger", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if st.button("Clear Ledger (Reset)", use_container_width=True):
        try:
            res = requests.post(f"{API_BASE}/clear")
            st.cache_data.clear()
            st.success(res.json().get("message", "Ledger cleared."))
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing ledger: {e}")


# --- Top Intro Block ---
st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <div class="logo-mark">F</div>
        <h1 style="margin:0; font-size: 2.2rem;">Fact Knowledge Layer</h1>
    </div>
    <p style="font-family: 'IBM Plex Sans', sans-serif; font-size: 1.1em; color: #2c2c2c; max-width: 800px; margin-bottom: 40px; line-height: 1.5;">
        Upload documents, extract factual claims, and automatically cross-reference evidence. This ledger provides an inspectable, deterministic record of corroborations and contradictions across your datasets.
    </p>
""", unsafe_allow_html=True)

# --- System Telemetry (Now immediately below intro) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Documents Ingested", len(set(f.get("document", "") for f in facts if f.get("document"))))
with col2:
    st.metric("Facts Extracted", len(facts))
with col3:
    st.metric("Relationships Found", len(relationships))
    
st.markdown("<br><hr style='border-top: 1px solid #d1cbbd;'><br>", unsafe_allow_html=True)

# --- How it Works / Pipeline ---
st.markdown("### Verification Pipeline")
st.markdown("""
<div style="font-family: 'IBM Plex Sans', sans-serif; color: #5e5c58; margin-bottom: 40px; max-width: 800px;">
    1. <strong>Page-Aware Extraction:</strong> PDFs are chunked while preserving exact page provenance.<br>
    2. <strong>Fact Extraction:</strong> Identifies explicit numerical and semantic facts deterministically.<br>
    3. <strong>Entity Normalization:</strong> Standardizes subjects, units, and time scopes for accurate comparison.<br>
    4. <strong>Relationship Reasoning:</strong> Identifies Corroborations, Contradictions, and Contextual differences.
</div>
""", unsafe_allow_html=True)


# --- Data Tabs (At the bottom) ---
tab1, tab2 = st.tabs(["Cross-Document Reasoning", "Knowledge Repository"])

with tab1:
    if relationships:
        for r in relationships:
            rel_type = r.get('relationship_type', 'Unknown')
            
            # Map type to CSS class
            css_class = "rel-failure"
            if "Corroboration" in rel_type: css_class = "rel-corroboration"
            elif "Contradiction" in rel_type: css_class = "rel-contradiction"
            elif "Contextual" in rel_type: css_class = "rel-contextual"
            
            st.markdown(f"""
            <div class="ledger-card">
                <span class="rel-banner {css_class}">{rel_type}</span>
                <p style="font-size: 1.1em; margin-bottom: 20px; font-family: 'Crimson Pro', serif; color: #111111;">
                    <strong>Verdict:</strong> {r.get('explanation', 'N/A')}
                </p>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div class="fact-col">
                        <div class="fact-col-title">Source Fact A</div>
                        <div style="color: #2c2c2c; font-weight: 500; margin-bottom: 10px;">{r.get('fact1', {}).get('statement', 'Unknown')}</div>
                        <div style="font-size: 0.85em; color: #5e5c58;">📄 {r.get('fact1', {}).get('document', 'Unknown')}</div>
                    </div>
                    <div class="fact-col">
                        <div class="fact-col-title">Source Fact B</div>
                        <div style="color: #2c2c2c; font-weight: 500; margin-bottom: 10px;">{r.get('fact2', {}).get('statement', 'Unknown')}</div>
                        <div style="font-size: 0.85em; color: #5e5c58;">📄 {r.get('fact2', {}).get('document', 'Unknown')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No relationships found. Extract facts from multiple documents to generate reasoning.")

with tab2:
    search_query = st.text_input("Filter Repository...", "")
    
    if facts:
        for f in facts:
            if search_query.lower() in f.get('statement', '').lower() or search_query.lower() in f.get('document', '').lower():
                st.markdown(f"""
                <div class="ledger-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <h4 style="margin-top: 0; margin-bottom: 8px; font-family: 'Crimson Pro', serif; color: #111111;">{f.get('statement', 'N/A')}</h4>
                            <p style="margin-bottom: 4px; font-size: 0.9em;"><strong>Entities:</strong> {', '.join(f.get('entities', []))}</p>
                            <p style="margin-bottom: 4px; font-size: 0.9em;"><strong>Time Scope:</strong> {f.get('time_scope', 'N/A')} | <strong>Units:</strong> {f.get('units', 'N/A')}</p>
                        </div>
                        <div style="text-align: right; margin-left: 20px;">
                            <span style="border: 1px solid #d1cbbd; color: #5e5c58; padding: 2px 6px; font-size: 0.75em; font-family: 'IBM Plex Sans', sans-serif;">Conf: {f.get('confidence', 0.0)}</span>
                        </div>
                    </div>
                    <hr style="border-color: #d1cbbd; border-style: solid; margin: 12px 0;">
                    <div style="font-size: 0.85em; color: #5e5c58;">
                        📄 Source: <strong>{f.get('document', 'Unknown')}</strong>
                        <br>
                        <em>"{f.get('evidence_quote', 'N/A')}"</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No facts extracted. Upload PDFs via the control panel.")
