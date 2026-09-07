from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    title = Column(String, nullable=True)
    facts = relationship("Fact", back_populates="document")

class Fact(Base):
    __tablename__ = "facts"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    statement = Column(String, index=True)
    entities = Column(String)  # JSON string
    units = Column(String, nullable=True)
    time_scope = Column(String, nullable=True)
    confidence = Column(Float)
    evidence_quote = Column(Text)
    page_number = Column(Integer)
    
    document = relationship("Document", back_populates="facts")

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True, index=True)
    fact1_id = Column(Integer, ForeignKey("facts.id"))
    fact2_id = Column(Integer, ForeignKey("facts.id"))
    relationship_type = Column(String) # Corroboration, Contradiction, Contextual Reconciliation
    explanation = Column(Text)
