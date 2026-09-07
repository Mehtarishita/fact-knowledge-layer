# Fact Knowledge Layer

This project implements a system to extract meaningful facts from PDFs, link them to evidence, and identify when facts across multiple documents corroborate, contradict, or can be reconciled through context.

## Setup and Run Instructions

### Prerequisites
- Python 3.10+
- Anthropic API Key (Claude 3.5 Sonnet is used for extraction and reasoning)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Mehtarishita/fact-knowledge-layer-
   cd fact-knowledge-layer-
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Copy `.env.example` to `.env` and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and set ANTHROPIC_API_KEY=your-key
   ```

### Running the Application
1. Start the FastAPI backend and frontend:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Open your browser to `http://localhost:8000`. You will see the application UI.
3. Drag and drop PDF files into the upload zone to ingest them. They will be processed in the background.

## Video Demo
<ADD DEMO VIDEO LINK HERE>

## Approach

- **PDF Ingestion:** PyMuPDF (`fitz`) is used to extract text while maintaining a mapping to the source page number.
- **Fact Extraction:** A chunk of text is sent to Claude 3.5 Sonnet using Anthropic's tool-calling API. We define a flexible Pydantic schema `Fact(statement, entities, units, time_scope, confidence, evidence_quote)`. This forces the LLM to output structured JSON without hardcoding the types of facts we care about.
- **Relationship Engine:** 
  1. As new facts are extracted, they are embedded using a local `sentence-transformers` model (`all-MiniLM-L6-v2`) via ChromaDB. This is fast, free, and reduces API calls.
  2. We query ChromaDB for the top 3 most similar existing facts.
  3. We pass the candidate pairs to Claude to categorize the relationship as Corroboration, Contradiction, Contextual Reconciliation, or Unrelated, along with an explanation.
- **Storage:** SQLite (via SQLAlchemy) is used for robust local storage of documents, facts, and relationships.
- **UI:** A sleek, vanilla HTML/CSS/JS frontend served directly by FastAPI. We used a modern dark-mode aesthetic with glassmorphism for a premium feel without the overhead of React/Next.js.

## Four Required Demo Cases
*(To be populated after pipeline execution on the starter datasets)*
1. **Corroboration**: TBD
2. **Genuine/likely contradiction**: TBD
3. **Apparent contradiction explained by context**: TBD
4. **An extraction or reasoning failure**: TBD

## Limitations and Next Steps
- **Chunking Strategy:** Currently, we extract text page by page. This might break facts that span across page boundaries. A rolling window chunking strategy with overlap would be more robust.
- **Table Extraction:** PyMuPDF gets text, but complex tables might lose structure. Using `pdfplumber` or `unstructured` for dedicated table extraction would improve financial data accuracy.
- **Scale:** Currently processing happens sequentially in the background. For large numbers of PDFs, a task queue like Celery + Redis would be better.

## Additional Notes
- The dataset used to test this includes excerpts from Delhivery's financial reports and India's macroeconomy reports. The schema-less LLM extraction successfully generalizes across both corporate finance and macroeconomic domains.
