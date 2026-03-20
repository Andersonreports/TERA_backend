from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_pdf(file_path, file_name):
    with open(file_path, "rb") as f:
        supabase.storage.from_("reports").upload(file_name, f)

    file_url = f"{SUPABASE_URL}/storage/v1/object/public/reports/{file_name}"
    return file_url
