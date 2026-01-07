# app/core/blob_storage.py
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_blob_info():
    """Parses connection string to get account details safely."""
    conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    conn_str_dict = dict(item.split('=', 1) for item in conn_str.split(';') if item)
    return {
        "account_name": conn_str_dict.get('AccountName') or conn_str_dict.get('accountname'),
        "account_key": conn_str_dict.get('AccountKey') or conn_str_dict.get('accountkey'),
        "container": settings.AZURE_CONTAINER_NAME
    }

def generate_write_sas_url(blob_name: str):
    """Generates a URL that allows the UI to UPLOAD (Write/Create)."""
    info = get_blob_info()
    
    now = datetime.now(timezone.utc)

    sas_token = generate_blob_sas(
        account_name=info["account_name"],
        account_key=info["account_key"],
        container_name=info["container"],
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True, write=True, create=True, list=True),
        start=now - timedelta(minutes=15),
        expiry=now + timedelta(hours=1)
    )
    
    # Construct the full URL the UI will use for PUT
    return f"https://{info['account_name']}.blob.core.windows.net/{info['container']}/{blob_name}?{sas_token}"

def generate_read_sas_url(blob_path: str):
    """Generates a URL that allows the Shore UI to VIEW (Read)."""
    info = get_blob_info()
    
    sas_token = generate_blob_sas(
        account_name=info["account_name"],
        account_key=info["account_key"],
        container_name=info["container"],
        blob_name=blob_path,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    
    return f"https://{info['account_name']}.blob.core.windows.net/{info['container']}/{blob_path}?{sas_token}"