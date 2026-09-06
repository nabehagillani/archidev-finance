"""
Minimal local-disk file storage for receipts and similar attachments.

Deliberately simple (no S3/object storage) so the app runs with zero
external setup — swap this module for a real object-storage client
later without touching callers, since everything else only calls
save_upload()/get_path() by company-scoped key.

Security: files are validated by declared content-type and a hard size
cap before being written, and stored under a per-company directory
keyed by a random filename (never the user-supplied name) so a
malicious filename can't be used for path traversal or to overwrite
another company's files.
"""
import os
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import settings


def _company_dir(company_id: str) -> str:
    path = os.path.join(settings.UPLOAD_DIR, company_id)
    os.makedirs(path, exist_ok=True)
    return path


def save_upload(company_id: str, file: UploadFile) -> str:
    if file.content_type not in settings.ALLOWED_RECEIPT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = file.file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 10MB upload limit")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    ext = os.path.splitext(file.filename or "")[1][:10]  # cap a pathological extension length
    stored_name = f"{uuid.uuid4()}{ext}"
    full_path = os.path.join(_company_dir(company_id), stored_name)

    with open(full_path, "wb") as f:
        f.write(contents)

    # Returned as a relative "key" (company_id/stored_name) rather than an
    # absolute path, matching how a real object-storage key would look.
    return f"{company_id}/{stored_name}"


def resolve_path(storage_key: str) -> str:
    """Turns a stored key back into a real filesystem path, guarding
    against path traversal in case a key was ever tampered with."""
    safe_key = storage_key.replace("..", "")
    return os.path.join(settings.UPLOAD_DIR, safe_key)
