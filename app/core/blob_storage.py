# app/core/blob_storage.py
import logging
from datetime import datetime, timedelta, timezone
from azure.storage.blob import (
    BlobServiceClient, 
    generate_blob_sas, 
    BlobSasPermissions,
    ContentSettings
)
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_blob_info():
    """Parses connection string to get account details safely."""
    conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
    
    # Handle both semicolon and newline-separated connection strings
    if ';' in conn_str:
        parts = [item for item in conn_str.split(';') if item and '=' in item]
    else:
        parts = [item for item in conn_str.split('\n') if item and '=' in item]
    
    conn_str_dict = {}
    for part in parts:
        key, value = part.split('=', 1)
        conn_str_dict[key.strip()] = value.strip()
    
    account_name = (conn_str_dict.get('AccountName') or 
                   conn_str_dict.get('accountname') or 
                   conn_str_dict.get('ACCOUNTNAME'))
    
    account_key = (conn_str_dict.get('AccountKey') or 
                  conn_str_dict.get('accountkey') or 
                  conn_str_dict.get('ACCOUNTKEY'))
    
    if not account_name or not account_key:
        logger.error(f"❌ Failed to parse connection string. Keys found: {list(conn_str_dict.keys())}")
        raise ValueError("Invalid Azure Storage connection string format")
    
    logger.info(f"✅ Parsed account: {account_name}, container: {settings.AZURE_CONTAINER_NAME}")
    
    return {
        "account_name": account_name,
        "account_key": account_key,
        "container": settings.AZURE_CONTAINER_NAME
    }

def generate_write_sas_url(blob_name: str):
    """
    Generates a URL that allows the UI to UPLOAD (Write/Create).
    Uses the latest Azure Storage API version.
    """
    info = get_blob_info()
    now = datetime.now(timezone.utc)
    
    # Start time 15 minutes in the past to handle clock skew
    start_time = now - timedelta(minutes=15)
    expiry_time = now + timedelta(hours=1)

    try:
        logger.info(f"🔧 Generating WRITE SAS for: {blob_name}")
        logger.info(f"   Account: {info['account_name']}")
        logger.info(f"   Container: {info['container']}")
        logger.info(f"   Start: {start_time.isoformat()}")
        logger.info(f"   Expiry: {expiry_time.isoformat()}")
        
        # Generate SAS token with explicit parameters
        sas_token = generate_blob_sas(
            account_name=info["account_name"],
            account_key=info["account_key"],
            container_name=info["container"],
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True, write=True, create=True),
            start=start_time,
            expiry=expiry_time
            # Note: 'version' parameter is handled automatically by SDK 12.28.0
        )
        
        # Debug: Log first 150 chars of SAS token to verify format
        logger.info(f"🔍 SAS Token (first 150 chars): {sas_token[:150]}...")
        
        # Verify 'sv' parameter exists in token
        if 'sv=' not in sas_token:
            logger.error("❌ SAS token missing 'sv' (storage version) parameter!")
            raise ValueError("Generated SAS token is invalid - missing version parameter")
        
        # Extract and log the sv value
        sv_start = sas_token.find('sv=') + 3
        sv_end = sas_token.find('&', sv_start) if '&' in sas_token[sv_start:] else len(sas_token)
        sv_value = sas_token[sv_start:sv_end]
        logger.info(f"✅ Storage Version (sv): {sv_value}")
        
        # Construct the full URL
        url = f"https://{info['account_name']}.blob.core.windows.net/{info['container']}/{blob_name}?{sas_token}"
        
        logger.info(f"✅ Generated write SAS URL successfully")
        logger.info(f"🔗 Full URL (first 200 chars): {url[:200]}...")
        
        return url
        
    except Exception as e:
        logger.error(f"❌ Failed to generate write SAS URL: {str(e)}", exc_info=True)
        raise

def generate_read_sas_url(blob_path: str):
    """
    Generates a URL that allows viewing/downloading (Read).
    Uses the latest Azure Storage API version.
    """
    info = get_blob_info()
    now = datetime.now(timezone.utc)
    expiry_time = now + timedelta(hours=24)  # 24 hours for viewing
    
    try:
        logger.info(f"🔧 Generating READ SAS for: {blob_path}")
        logger.info(f"   Account: {info['account_name']}")
        logger.info(f"   Container: {info['container']}")
        logger.info(f"   Expiry: {expiry_time.isoformat()}")
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=info["account_name"],
            account_key=info["account_key"],
            container_name=info["container"],
            blob_name=blob_path,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time
        )
        
        # Debug logging
        logger.info(f"🔍 SAS Token (first 150 chars): {sas_token[:150]}...")
        
        # Verify 'sv' parameter
        if 'sv=' not in sas_token:
            logger.error("❌ SAS token missing 'sv' parameter!")
            raise ValueError("Generated SAS token is invalid")
        
        # Extract sv value
        sv_start = sas_token.find('sv=') + 3
        sv_end = sas_token.find('&', sv_start) if '&' in sas_token[sv_start:] else len(sas_token)
        sv_value = sas_token[sv_start:sv_end]
        logger.info(f"✅ Storage Version (sv): {sv_value}")
        
        # Construct the full URL
        url = f"https://{info['account_name']}.blob.core.windows.net/{info['container']}/{blob_path}?{sas_token}"
        
        logger.info(f"✅ Generated read SAS URL successfully")
        
        return url
        
    except Exception as e:
        logger.error(f"❌ Failed to generate read SAS URL: {str(e)}", exc_info=True)
        raise

def get_blob_service_client():
    """
    Returns a BlobServiceClient instance for direct blob operations.
    """
    try:
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        
        logger.info("🔧 Initializing BlobServiceClient...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Test the connection
        logger.info("🧪 Testing connection to Azure Storage...")
        blob_service_client.get_service_properties()
        
        logger.info("✅ BlobServiceClient initialized and tested successfully")
        return blob_service_client
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize BlobServiceClient: {str(e)}", exc_info=True)
        raise

def verify_blob_exists(blob_path: str) -> bool:
    """
    Check if a blob exists in Azure Storage.
    Useful for debugging attachment access issues.
    """
    try:
        info = get_blob_info()
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(info["container"])
        blob_client = container_client.get_blob_client(blob_path)
        
        exists = blob_client.exists()
        logger.info(f"🔍 Blob exists check: {blob_path} -> {exists}")
        return exists
        
    except Exception as e:
        logger.error(f"❌ Error checking blob existence: {str(e)}")
        return False