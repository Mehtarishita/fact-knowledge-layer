import os
import requests
import time
import glob

DATA_DIR = "c:/Users/hp/OneDrive/Desktop/fact-knowledge-layer/data"
API_URL = "http://localhost:8000/api/upload"

def upload_pdfs():
    pdf_files = glob.glob(os.path.join(DATA_DIR, "**/*.pdf"), recursive=True)
    for pdf_file in pdf_files:
        print(f"Uploading {pdf_file}...")
        with open(pdf_file, "rb") as f:
            files = {"file": (os.path.basename(pdf_file), f, "application/pdf")}
            try:
                response = requests.post(API_URL, files=files)
                print(response.json())
            except Exception as e:
                print(f"Failed to upload {pdf_file}: {e}")

if __name__ == "__main__":
    upload_pdfs()
    print("Wait a bit for background tasks to process...")
    time.sleep(10)
    print("Done")
