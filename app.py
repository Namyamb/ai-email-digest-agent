import os
import csv
from datetime import date
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict
from main import run_digest_process
from invoice_extractor import OUTPUT_CSV, CSV_HEADERS, process_single_attachment

app = FastAPI(title="AI Email Digest & Invoice Hub")

# Track background job status
is_processing = False

def background_process():
    global is_processing
    try:
        run_digest_process()
    finally:
        is_processing = False

# Create static directory if not exists
os.makedirs("static", exist_ok=True)

@app.get("/api/invoices")
def get_invoices():
    """Reads the current day's CSV and returns it as JSON for the table."""
    v2_csv = OUTPUT_CSV.replace(".csv", "_v2.csv")
    files_to_read = [f for f in [OUTPUT_CSV, v2_csv] if os.path.exists(f)]

    if not files_to_read:
        return []

    data = []
    try:
        for target_file in files_to_read:
            with open(target_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return data

@app.get("/api/status")
def get_status():
    """Checks if a background process is currently running."""
    return {"is_processing": is_processing}

@app.post("/api/process")
def process_emails(background_tasks: BackgroundTasks):
    """Triggers the full processing pipeline in the background."""
    global is_processing
    if is_processing:
        return {"status": "Already processing"}
    
    is_processing = True
    background_tasks.add_task(background_process)
    return {"status": "Started processing"}

@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """Handles manual invoice upload and extraction with validation."""
    allowed_exts = {".pdf", ".docx", ".doc", ".csv", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_exts)}")

    try:
        content = await file.read()
        result_row = process_single_attachment(
            service=None,
            message_id="MANUAL_UPLOAD",
            email_subject="Manual Upload",
            filename=file.filename,
            file_bytes=content
        )
        return result_row
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.delete("/api/invoices")
def clear_invoices():
    """Deletes the current day's CSV files to clear the dashboard."""
    v2_csv = OUTPUT_CSV.replace(".csv", "_v2.csv")
    try:
        if os.path.exists(OUTPUT_CSV):
            os.remove(OUTPUT_CSV)
        if os.path.exists(v2_csv):
            os.remove(v2_csv)
        return {"status": "Successfully cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear: {str(e)}")

# Mount static files to serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
