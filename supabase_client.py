from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf(file_path, file_name):
    with open(file_path, "rb") as f:
        supabase.storage.from_("reports").upload(
            file_name,
            f,
            {"upsert": True}
        )

    url = supabase.storage.from_("reports").get_public_url(file_name)
    return url


def save_report(user_id, file_url, report_type):
    data = {
        "user_id": user_id,
        "file_url": file_url,
        "report_type": report_type
    }

    supabase.table("reports").insert(data).execute()
