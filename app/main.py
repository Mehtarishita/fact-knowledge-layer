from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import os
import json

from . import models, database, pdf_parser, llm_extractor, embeddings

# Create DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Fact Knowledge Layer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("./data/uploads", exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Fact Knowledge Layer API is running. Please start the Streamlit app."}

def process_pdf(filepath: str, filename: str, db: Session):
    try:
        # Create Document
        doc = models.Document(filename=filename, title=filename)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # 1. Parse PDF
        pages = pdf_parser.extract_text_from_pdf(filepath)
        
        # 2. Extract facts page by page
        for page in pages:
            text = page["text"]
            extracted_facts = llm_extractor.extract_facts_from_text(text)
            
            for ef in extracted_facts:
                db_fact = models.Fact(
                    document_id=doc.id,
                    statement=ef.statement,
                    entities=json.dumps(ef.entities),
                    units=ef.units,
                    time_scope=ef.time_scope,
                    confidence=ef.confidence,
                    evidence_quote=ef.evidence_quote,
                    page_number=page["page_number"]
                )
                db.add(db_fact)
                db.commit()
                db.refresh(db_fact)
                
                # 3. Add to Vector Store
                embeddings.add_fact_to_vectorstore(db_fact.id, db_fact.statement, filename)
                
                # 4. Find Similar Facts and Compare
                similar_facts = embeddings.find_similar_facts(db_fact.statement, top_k=3, exclude_fact_id=str(db_fact.id))
                
                for sim in similar_facts:
                    sim_fact = db.query(models.Fact).filter(models.Fact.id == sim["fact_id"]).first()
                    if sim_fact and sim_fact.document_id != db_fact.document_id:
                        # Compare them
                        relationship = llm_extractor.compare_facts(
                            fact1_statement=db_fact.statement,
                            fact1_time=db_fact.time_scope or "N/A",
                            fact1_units=db_fact.units or "N/A",
                            fact2_statement=sim_fact.statement,
                            fact2_time=sim_fact.time_scope or "N/A",
                            fact2_units=sim_fact.units or "N/A"
                        )
                        
                        if relationship and relationship.relationship_type != 'Unrelated':
                            db_rel = models.Relationship(
                                fact1_id=db_fact.id,
                                fact2_id=sim_fact.id,
                                relationship_type=relationship.relationship_type,
                                explanation=relationship.explanation
                            )
                            db.add(db_rel)
                            db.commit()

    except Exception as e:
        print(f"Error processing {filename}: {e}")

@app.post("/api/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    filepath = f"./data/uploads/{file.filename}"
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_pdf, filepath, file.filename, db)
    return {"message": "File uploaded and processing started in background."}

@app.get("/api/facts")
def get_facts(db: Session = Depends(database.get_db)):
    facts = db.query(models.Fact).all()
    result = []
    for f in facts:
        doc = db.query(models.Document).filter(models.Document.id == f.document_id).first()
        result.append({
            "id": f.id,
            "statement": f.statement,
            "entities": json.loads(f.entities) if f.entities else [],
            "units": f.units,
            "time_scope": f.time_scope,
            "confidence": f.confidence,
            "evidence_quote": f.evidence_quote,
            "page_number": f.page_number,
            "document": doc.filename if doc else "Unknown"
        })
    return result

@app.get("/api/relationships")
def get_relationships(db: Session = Depends(database.get_db)):
    rels = db.query(models.Relationship).all()
    result = []
    for r in rels:
        f1 = db.query(models.Fact).filter(models.Fact.id == r.fact1_id).first()
        f2 = db.query(models.Fact).filter(models.Fact.id == r.fact2_id).first()
        
        doc1 = db.query(models.Document).filter(models.Document.id == f1.document_id).first() if f1 else None
        doc2 = db.query(models.Document).filter(models.Document.id == f2.document_id).first() if f2 else None
        
        result.append({
            "id": r.id,
            "relationship_type": r.relationship_type,
            "explanation": r.explanation,
            "fact1": {
                "id": f1.id if f1 else None,
                "statement": f1.statement if f1 else "Unknown",
                "document": doc1.filename if doc1 else "Unknown"
            },
            "fact2": {
                "id": f2.id if f2 else None,
                "statement": f2.statement if f2 else "Unknown",
                "document": doc2.filename if doc2 else "Unknown"
            }
        })
    return result

@app.post("/api/clear")
def clear_ledger(db: Session = Depends(database.get_db)):
    db.query(models.Relationship).delete()
    db.query(models.Fact).delete()
    db.query(models.Document).delete()
    db.commit()
    try:
        from app.embeddings import collection
        collection.delete(where={"fact_id": {"$gte": 0}})
    except Exception as e:
        print(f"Failed to clear vector store: {e}")
    return {"message": "Ledger cleared successfully."}
