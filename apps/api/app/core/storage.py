from __future__ import annotations

from urllib.parse import quote

import httpx

from app.core.config import get_settings


class StorageError(RuntimeError):
    """Raised when a configured object store cannot complete an operation."""


def _settings_ready() -> tuple[str, str, str]:
    settings = get_settings()
    if not settings.supabase_url:
        raise StorageError("SUPABASE_URL is required for Supabase Storage")
    if not settings.supabase_service_role_key:
        raise StorageError("SUPABASE_SERVICE_ROLE_KEY is required for Supabase Storage")
    bucket = settings.report_storage_bucket
    if not bucket:
        raise StorageError("REPORT_STORAGE_BUCKET is required for Supabase Storage")
    return settings.supabase_url.rstrip("/"), settings.supabase_service_role_key, bucket


def _headers(service_key: str, content_type: str | None = None) -> dict[str, str]:
    headers = {"apikey": service_key}
    # Legacy service_role keys are JWTs; new sb_secret_* keys are opaque and
    # must only use the apikey header or Supabase rejects them as invalid JWTs.
    if not service_key.startswith("sb_"):
        headers["Authorization"] = f"Bearer {service_key}"
    if content_type:
        headers["Content-Type"] = content_type
    return headers


async def ensure_bucket(client: httpx.AsyncClient, base_url: str, service_key: str, bucket: str) -> None:
    response = await client.post(
        f"{base_url}/storage/v1/bucket",
        headers=_headers(service_key, "application/json"),
        json={
            "id": bucket,
            "name": bucket,
            "public": False,
            "file_size_limit": 10 * 1024 * 1024,
        },
    )
    if response.status_code in {200, 201, 400, 409}:
        return
    raise StorageError(f"Could not create report bucket ({response.status_code})")


async def upload_report(key: str, content: bytes, content_type: str) -> str:
    base_url, service_key, bucket = _settings_ready()
    object_url = f"{base_url}/storage/v1/object/{bucket}/{quote(key, safe='/')}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                object_url,
                headers=_headers(service_key, content_type),
                content=content,
            )
            if response.status_code == 404:
                await ensure_bucket(client, base_url, service_key, bucket)
                response = await client.post(
                    object_url,
                    headers=_headers(service_key, content_type),
                    content=content,
                )
    except httpx.HTTPError as exc:
        raise StorageError("Supabase Storage is temporarily unavailable") from exc
    if response.status_code not in {200, 201}:
        raise StorageError(f"Supabase Storage upload failed ({response.status_code})")
    return f"{bucket}/{key}"


async def download_report(key: str) -> bytes:
    base_url, service_key, bucket = _settings_ready()
    object_key = key.removeprefix(f"{bucket}/")
    object_url = f"{base_url}/storage/v1/object/{bucket}/{quote(object_key, safe='/')}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(object_url, headers=_headers(service_key))
    except httpx.HTTPError as exc:
        raise StorageError("Supabase Storage is temporarily unavailable") from exc
    if response.status_code != 200:
        raise StorageError(f"Supabase Storage download failed ({response.status_code})")
    return response.content
