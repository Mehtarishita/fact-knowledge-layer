import streamlit as st
import requests
import pandas as pd
import json
import base64
import os

# Configure page
st.set_page_config(page_title="Knowledge Layer", layout="wide", initial_sidebar_state="expanded")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# --- Premium Dark/Neon Custom CSS ---
st.markdown("""
    <style>
        /* Base Backgrounds & Colors */
        .stApp {
            background-color: #0b1121; /* Midnight Navy */
            color: #e2e8f0;
        }
        
        /* Main Headers */
        h1, h2, h3 {
            color: #f8fafc !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700 !important;
        }
        
        /* Neon Highlights */
        .neon-text {
            color: #22d3ee;
            text-shadow: 0 0 10px rgba(34, 211, 238, 0.4);
        }
        
        /* Cards */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .glass-card:hover {
            border-color: rgba(34, 211, 238, 0.5);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(34, 211, 238, 0.2);
            transform: translateY(-2px);
        }
        
        /* Relationship Specific Banners */
        .rel-banner {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }
        .rel-corroboration {
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .rel-contradiction {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .rel-contextual {
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .rel-failure {
            background: rgba(139, 92, 246, 0.15);
            color: #8b5cf6;
            border: 1px solid rgba(139, 92, 246, 0.3);
        }

        /* Metrics */
        div[data-testid="stMetricValue"] {
            color: #22d3ee;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            text-shadow: 0 0 15px rgba(34, 211, 238, 0.3);
        }
        
        /* Sidebar styling */
        .css-1544g2n {
            padding-top: 2rem;
        }
        
        /* Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.6);
            transform: scale(1.02);
            color: white;
        }
        
        /* Fix text colors inside cards */
        .glass-card p {
            color: #cbd5e1;
            font-size: 0.95em;
            line-height: 1.6;
        }
        .glass-card strong {
            color: #f8fafc;
        }
        
        /* Two-column layout for relationships */
        .fact-col {
            background: rgba(15, 23, 42, 0.6);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(51, 65, 85, 0.5);
            flex: 1 1 280px; /* Grow, shrink, but minimum 280px */
            min-width: 280px;
        }
        .fact-col-title {
            color: #94a3b8;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Evidence-Grounded Knowledge Layer")
st.markdown("<p style='color: #94a3b8; font-size: 1.1em;'>A deterministic extraction and reasoning engine for complex PDF documents.</p>", unsafe_allow_html=True)


# --- State & Data Fetching ---
@st.cache_data(ttl=5)
def fetch_data():
    try:
        facts = requests.get(f"{API_BASE}/facts").json()
        rels = requests.get(f"{API_BASE}/relationships").json()
        return facts, rels
    except:
        return [], []

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 class='neon-text'>Control Panel</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("Ingest Documents")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if st.button("Process Documents", use_container_width=True):
        if uploaded_files:
            with st.spinner("Processing & Extracting Knowledge..."):
                for f in uploaded_files:
                    files = {"file": (f.name, f, "application/pdf")}
                    res = requests.post(f"{API_BASE}/upload", files=files)
                    if res.status_code == 200:
                        st.success(f"Processed: {f.name}")
                    else:
                        st.error(f"Failed: {f.name}")
            st.cache_data.clear()
            st.rerun()
            
    st.markdown("---")
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

facts, relationships = fetch_data()

# --- Main Layout (Tabs) ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Knowledge Repository", "⚖️ Cross-Document Reasoning"])

with tab1:
    st.markdown("### System Telemetry")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents Ingested", len(set(f.get("document", "") for f in facts if f.get("document"))))
    with col2:
        st.metric("Facts Extracted", len(facts))
    with col3:
        st.metric("Relationships Found", len(relationships))
        
    st.markdown("---")
    st.markdown("### How it Works")
    st.markdown("""
    **Pipeline Architecture:**
    1. **Page-Aware Extraction:** PDFs are chunked natively while preserving page provenance.
    2. **Fact Extraction:** Identifies both explicit numerical and semantic facts deterministically.
    3. **Entity Normalization:** Standardizes subjects, units, and time scopes.
    4. **Relationship Reasoning:** Uses set-theory and cross-document heuristics to identify Corroborations, Contradictions, and Contextual differences deterministically.
    """)

with tab2:
    st.markdown("### Extracted Facts Repository")
    search_query = st.text_input("Filter Facts by Keyword...", "")
    
    if facts:
        for f in facts:
            if search_query.lower() in f.get('statement', '').lower() or search_query.lower() in f.get('document', '').lower():
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <h4 style="margin-top: 0; margin-bottom: 8px;">{f.get('statement', 'N/A')}</h4>
                            <p style="margin-bottom: 4px;"><strong>Entities:</strong> {', '.join(f.get('entities', []))}</p>
                            <p style="margin-bottom: 4px;"><strong>Time Scope:</strong> {f.get('time_scope', 'N/A')} | <strong>Units:</strong> {f.get('units', 'N/A')}</p>
                        </div>
                        <div style="text-align: right; margin-left: 20px;">
                            <span style="background: rgba(34, 211, 238, 0.1); color: #22d3ee; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; white-space: nowrap;">Conf: {f.get('confidence', 0.0)}</span>
                        </div>
                    </div>
                    <hr style="border-color: rgba(148, 163, 184, 0.2); margin: 12px 0;">
                    <div style="font-size: 0.85em; color: #64748b;">
                        📄 Source: <strong>{f.get('document', 'Unknown')}</strong>
                        <br>
                        <em>"{f.get('evidence_quote', 'N/A')}"</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No facts extracted yet. Upload some PDFs in the control panel.")

with tab3:
    st.markdown("### Cross-Document Reasoning Engine")
    
    if relationships:
        for r in relationships:
            rel_type = r.get('relationship_type', 'Unknown')
            
            # Map type to CSS class
            css_class = "rel-failure"
            if "Corroboration" in rel_type: css_class = "rel-corroboration"
            elif "Contradiction" in rel_type: css_class = "rel-contradiction"
            elif "Contextual" in rel_type: css_class = "rel-contextual"
            
            st.markdown(f"""
            <div class="glass-card">
                <span class="rel-banner {css_class}">{rel_type}</span>
                <p style="font-size: 1.1em; margin-bottom: 20px;"><strong>Verdict:</strong> {r.get('explanation', 'N/A')}</p>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div class="fact-col">
                        <div class="fact-col-title">Fact A</div>
                        <div style="color: #f8fafc; font-weight: 500; margin-bottom: 10px;">{r.get('fact1', {}).get('statement', 'Unknown')}</div>
                        <div style="font-size: 0.8em; color: #94a3b8;">📄 {r.get('fact1', {}).get('document', 'Unknown')}</div>
                    </div>
                    <div class="fact-col">
                        <div class="fact-col-title">Fact B</div>
                        <div style="color: #f8fafc; font-weight: 500; margin-bottom: 10px;">{r.get('fact2', {}).get('statement', 'Unknown')}</div>
                        <div style="font-size: 0.8em; color: #94a3b8;">📄 {r.get('fact2', {}).get('document', 'Unknown')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No relationships found yet. Extract facts from multiple documents to see reasoning.")
