import fitz  # PyMuPDF
import os

def extract_text_from_pdf(filepath: str):
    """
    Extracts text from a PDF file page by page.
    Returns a list of dicts: [{"page_number": int, "text": str}]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    doc = fitz.open(filepath)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        
        # Clean up text a bit (remove excessive newlines)
        text = " ".join(text.split())
        
        if text.strip():
            pages.append({
                "page_number": page_num + 1,
                "text": text
            })
            
    return pages
