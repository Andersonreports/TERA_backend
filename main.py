from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


import pandas as pd
import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"
import uuid
import math
import fitz

from tera_template import TERAReportGenerator
from fastapi.staticfiles import StaticFiles
import base64
import io
from reportlab.lib.utils import ImageReader
from supabase_client import supabase
from supabase_client import upload_pdf, save_report
import uuid




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMP_DIR = os.path.join(BASE_DIR, "temp")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")
@app.get("/")
def root():
    return {"status": "TERA backend running"}


# -------- Preview Report --------
@app.post("/preview")
async def preview_report(data: dict):

    print("REQUEST DATA:",data)
    file_id = str(uuid.uuid4()) + ".pdf"
    filepath = os.path.join(TEMP_DIR, file_id)

    gen = TERAReportGenerator(data, TEMP_DIR)
    gen.filepath = filepath
    gen.filename = file_id

    gen.generate()

    return {"preview_url": f"/preview-file/{file_id}"}
    

@app.get("/preview-file/{filename}")
def preview_file(filename: str):

    path = os.path.join(TEMP_DIR, filename)

    return FileResponse(path, media_type="application/pdf")


# -------- Single Report Generation --------
@app.post("/generate")
async def generate_report(data: dict):

    try:
        generator = TERAReportGenerator(data, REPORT_DIR)
        pdf_path = generator.generate()

        # check if file exists
        if not pdf_path or not os.path.exists(pdf_path):
            return {"error": "PDF not generated"}

        report_id = str(uuid.uuid4())
        user_id = "user1"

        file_name = f"{user_id}/{report_id}.pdf"

        # upload to Supabase
        file_url = upload_pdf(pdf_path, file_name)

        # save to DB
        save_report(user_id, file_url, "tera")

        return {
            "status": "success",
            "file_url": file_url
        }

    except Exception as e:
        return {"error": str(e)}
        
# -------- Bulk Report Generation --------
@app.post("/generate-bulk")
async def generate_bulk(data: list):

    output_files = []

    for row in data:

        generator = TERAReportGenerator(row, REPORT_DIR)
        pdf_path = generator.generate()

        # ✅ NEW CODE STARTS HERE
        report_id = str(uuid.uuid4())
        user_id = "user1"  # you can change later

        file_name = f"{user_id}/{report_id}.pdf"

        # upload to Supabase
        file_url = upload_pdf(pdf_path, file_name)

        # save to database
        save_report(user_id, file_url, "tera")

        output_files.append({
            "file_name": os.path.basename(pdf_path),
            "file_url": file_url
        })
        # ✅ NEW CODE ENDS HERE

    return {
        "generated": output_files
    }


# -------- Compare PDFs --------
@app.post("/compare-pdf")
async def compare_pdf(file1: UploadFile = File(...), file2: UploadFile = File(...)):

    pdf1 = fitz.open(stream=file1.file.read(), filetype="pdf")
    pdf2 = fitz.open(stream=file2.file.read(), filetype="pdf")

    text1 = ""
    text2 = ""

    for page in pdf1:
        text1 += page.get_text()

    for page in pdf2:
        text2 += page.get_text()

    differences = []

    lines1 = text1.splitlines()
    lines2 = text2.splitlines()

    for i in range(min(len(lines1), len(lines2))):
        if lines1[i] != lines2[i]:
            differences.append({
                "line": i,
                "left": lines1[i],
                "right": lines2[i]
            })

    return {"differences": differences}


# -------- Excel Upload --------
@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):

    df = pd.read_excel(file.file)

    rows = df.to_dict(orient="records")

    # Convert NaN values to None
    for row in rows:
        for key, value in row.items():
            if isinstance(value, float) and math.isnan(value):
                row[key] = None

    return {"rows": rows}

@app.get("/test-db")
def test_db():
    response = supabase.table("reports").select("*").execute()
    return response.data


