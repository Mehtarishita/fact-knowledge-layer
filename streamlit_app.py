import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Fact Knowledge Layer - Verifier's Ledger", layout="wide")

API_BASE = "http://localhost:8000/api"

# Inject Custom CSS for Advanced Relationship Layouts
st.markdown("""
<style>
/* CSS for Relationship Cards */
:root {
    --bg-color: #0f172a;
    --surface-bg: #1e293b;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --border-color: #334155;
    
    --rel-corroboration: #10b981;
    --rel-corroboration-bg: #064e3b;
    
    --rel-contradiction: #ef4444;
    --rel-contradiction-bg: #7f1d1d;
    
    --rel-contextual: #3b82f6;
    --rel-contextual-bg: #1e3a8a;

    --rel-failure: #f59e0b;
    --rel-failure-bg: #78350f;
}
.relationship-card {
    background: var(--surface-bg);
    border: 1px solid var(--border-color);
    padding: 1.5rem;
    position: relative;
    border-radius: 8px;
    margin-bottom: 1rem;
    color: var(--text-primary);
}
.rel-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.75rem;
}
.rel-type {
    font-weight: 700;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.rel-reasoning {
    font-size: 0.95rem;
    color: var(--text-primary);
    font-weight: 500;
    max-width: 70%;
}
.fact-box-statement { font-weight: 600; margin-bottom: 0.5rem; font-size: 1rem; }
.fact-box-meta { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }

/* Distinct Layouts */
.layout-corroboration .rel-body { display: flex; flex-direction: column; gap: 1rem; border-left: 4px solid var(--rel-corroboration); padding-left: 1rem; }
.layout-corroboration .rel-type { color: var(--rel-corroboration); }

.layout-contradiction .rel-body { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; position: relative; }
.layout-contradiction .rel-body::after {
    content: "VS"; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
    background: var(--surface-bg); color: var(--rel-contradiction); font-weight: 700;
    padding: 0.5rem; border: 1px solid var(--rel-contradiction); border-radius: 50%; font-size: 0.75rem;
}
.layout-contradiction .fact-box { border-top: 4px solid var(--rel-contradiction); padding-top: 1rem; }
.layout-contradiction .rel-type { color: var(--rel-contradiction); }

.layout-contextual .rel-body { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.layout-contextual .fact-box { border-left: 2px dashed var(--rel-contextual); padding-left: 1rem; }
.layout-contextual .rel-type { color: var(--rel-contextual); }

.layout-failure { background: var(--rel-failure-bg); border-color: var(--rel-failure); }
.layout-failure .rel-type { color: var(--rel-failure); }
.layout-failure .rel-reasoning { font-family: Consolas, monospace; color: var(--rel-failure); }
.layout-failure .rel-body { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.layout-failure .fact-box { border-top: 2px dotted var(--rel-failure); padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# Helper function to fetch data from FastAPI backend
@st.cache_data(ttl=3)
def fetch_data():
    try:
        facts_res = requests.get(f"{API_BASE}/facts")
        rels_res = requests.get(f"{API_BASE}/relationships")
        return facts_res.json(), rels_res.json()
    except Exception as e:
        return [], []

def upload_file(uploaded_file):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    try:
        res = requests.post(f"{API_BASE}/upload", files=files)
        return res.json().get("message", "Success")
    except Exception as e:
        return f"Error: {e}"

# UI Layout
st.sidebar.title("Verifier's Ledger")

uploaded_files = st.sidebar.file_uploader("Ingest Documents (PDF)", type=["pdf"], accept_multiple_files=True)
if st.sidebar.button("Upload & Ingest"):
    for f in uploaded_files:
        with st.spinner(f"Uploading {f.name}..."):
            msg = upload_file(f)
            st.sidebar.success(msg)

if st.sidebar.button("Sync Ledger"):
    st.cache_data.clear()

facts, relationships = fetch_data()

# Processing Stats
unique_docs = len(set([f['document'] for f in facts])) if facts else 0

st.sidebar.header("Ledger Statistics")
col1, col2, col3 = st.sidebar.columns(3)
col1.metric("Docs", unique_docs)
col2.metric("Facts", len(facts))
col3.metric("Rels", len(relationships))

# Required Demo Cases Checklist
st.sidebar.header("Required Demo Cases")
seen_corr = any("Corroboration" in r['relationship_type'] for r in relationships) if relationships else False
seen_cont = any("Contradiction" in r['relationship_type'] for r in relationships) if relationships else False
seen_ctx = any("Contextual" in r['relationship_type'] for r in relationships) if relationships else False
seen_fail = any("Failure" in r['relationship_type'] for r in relationships) if relationships else False

st.sidebar.checkbox("Corroboration", value=seen_corr, disabled=True)
st.sidebar.checkbox("Contradiction", value=seen_cont, disabled=True)
st.sidebar.checkbox("Contextual Reconciliation", value=seen_ctx, disabled=True)
st.sidebar.checkbox("Extraction Failure", value=seen_fail, disabled=True)

search_query = st.sidebar.text_input("Filter Facts...")

if not facts:
    st.info("Awaiting Documents. Upload a PDF in the sidebar to begin extraction and cross-referencing.")
else:
    st.header("Cross-Document Relationships")
    # Deduplicate relationships
    grouped_rels = {}
    for r in relationships:
        # Filter logic
        if search_query and search_query.lower() not in r['fact1']['statement'].lower() and search_query.lower() not in r['fact2']['statement'].lower():
            continue
            
        key = "|".join(sorted([r['fact1']['statement'], r['fact2']['statement']])) + "|" + r['relationship_type']
        if key not in grouped_rels:
            grouped_rels[key] = {**r, "count": 0}
        grouped_rels[key]["count"] += 1
        
    if grouped_rels:
        for rel in grouped_rels.values():
            layout_class = "layout-unrelated"
            if "Corroboration" in rel['relationship_type']: layout_class = "layout-corroboration"
            elif "Contradiction" in rel['relationship_type']: layout_class = "layout-contradiction"
            elif "Contextual" in rel['relationship_type']: layout_class = "layout-contextual"
            elif "Failure" in rel['relationship_type']: layout_class = "layout-failure"
            
            badge = f"<span style='background:var(--border-color); padding:0.2rem 0.5rem; border-radius:12px; margin-left:1rem; font-size:0.75rem'>Seen in {rel['count']} document pairs</span>" if rel['count'] > 1 else ""
            
            html = f"""
            <div class="relationship-card {layout_class}">
                <div class="rel-header">
                    <div><span class="rel-type">{rel['relationship_type']}</span>{badge}</div>
                    <span class="rel-reasoning">{rel['explanation']}</span>
                </div>
                <div class="rel-body">
                    <div class="fact-box">
                        <div class="fact-box-statement">{rel['fact1']['statement']}</div>
                        <div class="fact-box-meta">{rel['fact1']['document']}</div>
                    </div>
                    <div class="fact-box">
                        <div class="fact-box-statement">{rel['fact2']['statement']}</div>
                        <div class="fact-box-meta">{rel['fact2']['document']}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.write("No relationships match the filter.")
        
    st.header("Extracted Facts Repository")
    # Deduplicate facts
    grouped_facts = {}
    for f in facts:
        if search_query and search_query.lower() not in f['statement'].lower():
            continue
        if f['statement'] not in grouped_facts:
            meta_str = " | ".join(filter(None, [f.get('time_scope'), f.get('units')]))
            grouped_facts[f['statement']] = {"statement": f['statement'], "meta": meta_str, "evidence": []}
        grouped_facts[f['statement']]["evidence"].append(f)
        
    for g in grouped_facts.values():
        label = f"{g['statement']} ({g['meta']})" if g['meta'] else g['statement']
        with st.expander(label):
            for e in g['evidence']:
                st.markdown(f"> *{e['evidence_quote']}*")
                st.caption(f"Source: **{e['document']}** (Page {e['page_number']}) | Confidence: {int(e['confidence']*100)}%")
