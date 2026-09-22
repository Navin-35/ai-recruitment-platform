import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.supabase import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)

LOCAL_STORAGE_ROOT = Path("data/storage")


class StorageService:
    """
    Unified Storage Service supporting private Supabase Storage buckets
    with automatic fallback to local disk storage when running in dev/test mode.
    """

    def __init__(self):
        LOCAL_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    @property
    def is_cloud(self) -> bool:
        return is_supabase_configured()

    def upload_file(
        self,
        bucket: str,
        destination_path: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Uploads file bytes to the specified bucket.
        Returns the stored file identifier/path.
        """
        if self.is_cloud:
            supabase = get_supabase_client()
            if supabase:
                try:
                    res = supabase.storage.from_(bucket).upload(
                        path=destination_path,
                        file=file_bytes,
                        file_options={"content-type": content_type, "upsert": "true"},
                    )
                    logger.info("Uploaded to Supabase bucket '%s': %s", bucket, destination_path)
                    return destination_path
                except Exception as e:
                    logger.warning("Supabase storage upload failed: %s. Falling back to local.", e)

        # Local fallback
        local_path = LOCAL_STORAGE_ROOT / bucket / destination_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(file_bytes)
        return str(local_path)

    def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generates a secure, time-limited signed URL for viewing/downloading the file.
        """
        expiry = expires_in or settings.storage_signed_url_expiry

        if self.is_cloud:
            supabase = get_supabase_client()
            if supabase:
                try:
                    signed_res = supabase.storage.from_(bucket).create_signed_url(
                        path=file_path,
                        expires_in=expiry,
                    )
                    if isinstance(signed_res, dict) and "signedURL" in signed_res:
                        return signed_res["signedURL"]
                    elif hasattr(signed_res, "signed_url"):
                        return signed_res.signed_url
                    elif isinstance(signed_res, str):
                        return signed_res
                except Exception as e:
                    logger.warning("Supabase signed URL creation failed: %s. Using local fallback.", e)

        # Local fallback representation
        local_path = LOCAL_STORAGE_ROOT / bucket / file_path
        if local_path.exists():
            return f"/api/v1/storage/{bucket}/{file_path}?token=local-dev-preview"
        return f"/local-file/{file_path}"

    def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Downloads file bytes from storage.
        """
        if self.is_cloud:
            supabase = get_supabase_client()
            if supabase:
                try:
                    return supabase.storage.from_(bucket).download(file_path)
                except Exception as e:
                    logger.warning("Supabase download failed: %s. Trying local.", e)

        local_path = LOCAL_STORAGE_ROOT / bucket / file_path
        if local_path.exists():
            return local_path.read_bytes()

        alt_local = Path(file_path)
        if alt_local.exists():
            return alt_local.read_bytes()

        raise FileNotFoundError(f"File not found in storage: {bucket}/{file_path}")

    def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Deletes a file from the bucket.
        """
        deleted = False

        if self.is_cloud:
            supabase = get_supabase_client()
            if supabase:
                try:
                    supabase.storage.from_(bucket).remove([file_path])
                    deleted = True
                except Exception as e:
                    logger.warning("Supabase file delete failed: %s", e)

        local_path = LOCAL_STORAGE_ROOT / bucket / file_path
        if local_path.exists():
            try:
                local_path.unlink()
                deleted = True
            except OSError:
                pass

        alt_local = Path(file_path)
        if alt_local.exists():
            try:
                alt_local.unlink()
                deleted = True
            except OSError:
                pass

        return deleted


storage_service = StorageService()
