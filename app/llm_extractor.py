import os
import json
import anthropic
from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedFact(BaseModel):
    statement: str = Field(description="A clear, normalized statement of the fact (e.g., 'EBITDA was positive', 'Real GDP growth was 6.5%').")
    entities: List[str] = Field(description="Key entities or subjects mentioned (e.g., 'Delhivery', 'India', 'EBITDA', 'GDP').")
    units: Optional[str] = Field(description="The units of the fact if numerical (e.g., '₹ Cr', '%', 'USD'). Leave null if not applicable.")
    time_scope: Optional[str] = Field(description="The time scope or period this fact applies to (e.g., 'FY24', 'Q4 FY24', '2024-25', 'FY2019-FY2021').")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0 based on how explicitly this is stated in the text.")
    evidence_quote: str = Field(description="The EXACT quote from the text that proves this fact. Must be an exact substring.")

class FactExtractionResult(BaseModel):
    facts: List[ExtractedFact]

def extract_facts_from_text(text: str) -> List[ExtractedFact]:
    """
    Uses Anthropic to extract structured facts from a chunk of text, falling back to a smart mock if API key is missing.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your-api-key-here":
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = "You are an expert financial and macroeconomic analyst. Extract meaningful numerical and semantic facts."
        tools = [{"name": "record_facts", "description": "Record facts", "input_schema": FactExtractionResult.model_json_schema()}]
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620", max_tokens=4096, system=system_prompt, tools=tools,
                tool_choice={"type": "tool", "name": "record_facts"}, messages=[{"role": "user", "content": f"Extract facts:\n\n{text}"}]
            )
            for content in response.content:
                if content.type == "tool_use" and content.name == "record_facts":
                    return FactExtractionResult.model_validate(content.input).facts
        except Exception as e:
            print(f"API Error: {e}")    # Fallback to Mock Extractor for Demo
    facts = []
    # Generic Heuristic for ANY unknown PDF
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15 or len(sentence) > 500:
            continue
        
        # Look for numerical facts or strong semantic keywords
        if re.search(r'\d+', sentence) and re.search(r'(%|percent|margin|revenue|profit|loss|gdp|growth|\$|crore|million|billion|increase|decrease|total|amount|rate)', sentence, re.IGNORECASE):
            units = None
            if "%" in sentence or "percent" in sentence.lower(): units = "%"
            elif "$" in sentence or "USD" in sentence: units = "USD"
            elif "Rs" in sentence or "INR" in sentence or "crore" in sentence.lower(): units = "INR"
                
            facts.append(ExtractedFact(
                statement=sentence[:150] + ("..." if len(sentence) > 150 else ""),
                entities=["Extracted Subject"],
                units=units,
                time_scope="Unknown",
                confidence=0.75,
                evidence_quote=sentence[:250]
            ))
            
            if len(facts) >= 3: # Limit to 3 facts per chunk
                break

    return facts

class RelationshipResult(BaseModel):
    relationship_type: str = Field(description="Must be one of: 'Corroboration', 'Contradiction', 'Contextual Reconciliation', 'Extraction Failure', 'Unrelated'")
    explanation: str = Field(description="A concise explanation of why this relationship exists.")

def compare_facts(fact1_statement: str, fact1_time: str, fact1_units: str,
                  fact2_statement: str, fact2_time: str, fact2_units: str) -> Optional[RelationshipResult]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your-api-key-here":
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = "You are an expert analyst. Determine if facts Corroborate, Contradict, or Reconcile."
        tools = [{"name": "record_relationship", "description": "Record relationship", "input_schema": RelationshipResult.model_json_schema()}]
        try:
            prompt = f"Fact 1: {fact1_statement}\nFact 2: {fact2_statement}"
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620", max_tokens=1024, system=system_prompt, tools=tools,
                tool_choice={"type": "tool", "name": "record_relationship"}, messages=[{"role": "user", "content": prompt}]
            )
            for content in response.content:
                if content.type == "tool_use" and content.name == "record_relationship":
                    return RelationshipResult.model_validate(content.input)
        except Exception as e:
            print(f"Error during comparison: {e}")

    # Mock Relationship Engine
    f1 = fact1_statement.lower()
    f2 = fact2_statement.lower()
    
    # Dynamic Heuristic for unknown PDFs
    import re
    words1 = set(re.findall(r'\b[a-z]{4,}\b', f1))
    words2 = set(re.findall(r'\b[a-z]{4,}\b', f2))
    overlap = words1.intersection(words2)
    
    if len(overlap) >= 2:
        nums1 = set(re.findall(r'\d+\.?\d*', f1))
        nums2 = set(re.findall(r'\d+\.?\d*', f2))
        years1 = set(re.findall(r'20\d{2}', f1))
        years2 = set(re.findall(r'20\d{2}', f2))
        
        # Remove years from numbers to only compare metrics
        nums1 = nums1 - years1
        nums2 = nums2 - years2
        
        # Check for Contextual Reconciliation (different years/timeframes)
        if years1 and years2 and not years1.intersection(years2):
            return RelationshipResult(
                relationship_type="Contextual Reconciliation",
                explanation=f"Facts share topics ({', '.join(overlap)}) but refer to different time periods ({', '.join(years1)} vs {', '.join(years2)})."
            )
            
        # Check for numbers
        if nums1 and nums2:
            if not nums1.intersection(nums2):
                return RelationshipResult(
                    relationship_type="Contradiction",
                    explanation=f"Facts discuss similar topics ({', '.join(overlap)}) but contain conflicting numbers."
                )
            else:
                return RelationshipResult(
                    relationship_type="Corroboration",
                    explanation=f"Facts discuss the same topic ({', '.join(overlap)}) and align on numerical values."
                )
        else:
            # If no numbers, but share words, just mark as Extraction Failure due to ambiguity
            return RelationshipResult(
                relationship_type="Extraction Failure",
                explanation=f"Facts share topics ({', '.join(overlap)}) but lack specific numbers for confident comparison."
            )
            
    return None




