import pytest
from fastapi.testclient import TestClient
from app.main import app, process_pdf
from app import database, models
import os

client = TestClient(app)

def test_dynamic_pipeline():
    # 1. Clear the ledger
    response = client.post("/api/clear")
    assert response.status_code == 200

    # 2. Add two documents directly to the database via process_pdf
    # We will simulate PDF extraction by just mocking pdf_parser to return our text
    import app.pdf_parser as pdf_parser
    
    # Store original
    original_extract = pdf_parser.extract_text_from_pdf
    
    # Text 1: 15% revenue growth in 2024
    def mock_extract_1(filepath):
        return [{"page_number": 1, "text": "The company reported a massive 15% revenue increase in 2024, beating expectations."}]
    
    # Text 2: 12% revenue growth in 2024
    def mock_extract_2(filepath):
        return [{"page_number": 1, "text": "Financial statements indicate a 12% revenue increase in 2024 across all sectors."}]
    
    db = database.SessionLocal()
    try:
        # Process Doc 1
        pdf_parser.extract_text_from_pdf = mock_extract_1
        process_pdf("dummy1.pdf", "Doc1.pdf", db)
        
        # Process Doc 2
        pdf_parser.extract_text_from_pdf = mock_extract_2
        process_pdf("dummy2.pdf", "Doc2.pdf", db)
        
        # 3. Check Facts
        facts_res = client.get("/api/facts").json()
        assert len(facts_res) == 2, f"Expected 2 facts, got {len(facts_res)}"
        
        # 4. Check Relationships
        rels_res = client.get("/api/relationships").json()
        
        # We expect 1 relationship, and it should be a Contradiction
        # Because the texts share "revenue", "increase", "2024" but have different numbers (15 vs 12)
        assert len(rels_res) == 1, f"Expected 1 relationship, got {len(rels_res)}"
        
        rel = rels_res[0]
        assert rel["relationship_type"] == "Contradiction", f"Expected Contradiction, got {rel['relationship_type']}"
        assert "conflicting numbers" in rel["explanation"].lower()
        
        # Document names should match exactly what we passed
        assert {rel["fact1"]["document"], rel["fact2"]["document"]} == {"Doc1.pdf", "Doc2.pdf"}
        
    finally:
        pdf_parser.extract_text_from_pdf = original_extract
        db.close()
