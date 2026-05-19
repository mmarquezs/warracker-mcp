"""Async HTTP client for the Warracker REST API.

Authentication uses JWT only:
  POST /api/auth/login with {username, password} returns a Bearer token.
  All subsequent requests use Authorization: Bearer <token>.
  On 401, the client re-authenticates automatically.

Environment variables:
  WARRACKER_URL      - base URL, e.g. http://10.0.0.143:80
  WARRACKER_USERNAME - local user (non-OIDC)
  WARRACKER_PASSWORD - user password
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

_TIMEOUT = 30.0
_UPLOAD_TIMEOUT = 120.0

logger = logging.getLogger("warracker_mcp")


class WarrackerError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WarrackerClient:
    def __init__(self) -> None:
        base_url = os.environ.get("WARRACKER_URL", "").rstrip("/")
        if not base_url:
            raise ValueError("WARRACKER_URL environment variable is required")

        username = os.environ.get("WARRACKER_USERNAME", "")
        password = os.environ.get("WARRACKER_PASSWORD", "")
        if not username or not password:
            raise ValueError(
                "WARRACKER_USERNAME and WARRACKER_PASSWORD environment variables are required"
            )

        self._base = base_url
        self._username = username
        self._password = password
        self._token: str | None = None

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _login(self) -> None:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
            r = await c.post(
                self._url("/api/auth/login"),
                json={"username": self._username, "password": self._password},
            )
            if r.status_code != 200:
                raise WarrackerError(
                    f"Authentication failed (HTTP {r.status_code}): {r.text}",
                    status_code=r.status_code,
                )
            data = r.json()
            self._token = data.get("token") or data.get("access_token")
            if not self._token:
                raise WarrackerError(
                    f"Authentication response did not contain a token: {list(data.keys())}"
                )

    async def _ensure_token(self) -> None:
        if not self._token:
            await self._login()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        retry_on_401: bool = True,
        **kwargs: Any,
    ) -> Any:
        await self._ensure_token()
        request_headers = {**self._auth_headers(), **(headers or {})}
        timeout = kwargs.pop("timeout", _TIMEOUT)

        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.request(method, self._url(path), headers=request_headers, **kwargs)

            if r.status_code == 401 and retry_on_401:
                await self._login()
                request_headers = {**self._auth_headers(), **(headers or {})}
                r = await c.request(method, self._url(path), headers=request_headers, **kwargs)

            if r.status_code >= 400:
                detail = r.text
                try:
                    body = r.json()
                    if isinstance(body, dict):
                        detail = body.get("error") or body.get("message") or body.get("msg") or r.text
                except Exception:
                    pass
                raise WarrackerError(
                    f"Warracker API error (HTTP {r.status_code}): {detail}",
                    status_code=r.status_code,
                )

            if not r.content:
                return {}
            return r.json()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post_json(self, path: str, data: dict[str, Any]) -> Any:
        return await self._request("POST", path, json=data)

    async def post_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    ) -> Any:
        return await self._request(
            "POST",
            path,
            data=data,
            files=files,
            headers={"Accept": "application/json"},
            timeout=_UPLOAD_TIMEOUT,
        )

    async def put_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    ) -> Any:
        return await self._request(
            "PUT",
            path,
            data=data,
            files=files,
            headers={"Accept": "application/json"},
            timeout=_UPLOAD_TIMEOUT,
        )

    async def list_warranties(self, params: dict[str, Any] | None = None) -> Any:
        return await self.get("/api/warranties", params=params)

    async def get_warranty(self, warranty_id: int) -> Any:
        results = await self.get("/api/warranties", params={"id": warranty_id})
        if isinstance(results, list) and len(results) > 0:
            return results[0]
        if isinstance(results, dict):
            return results
        return {"error": f"Warranty {warranty_id} not found"}

    async def create_warranty(
        self,
        fields: dict[str, Any],
        file_uploads: list[tuple[str, str, bytes]] | None = None,
    ) -> Any:
        data: dict[str, Any] = {}
        for key, value in fields.items():
            if value is None:
                continue
            if key == "serial_numbers" and isinstance(value, list):
                for sn in value:
                    data.setdefault("serial_numbers[]", [])
                    if isinstance(data["serial_numbers[]"], list):
                        data["serial_numbers[]"].append(sn)
                continue
            if key == "is_lifetime":
                data[key] = "true" if value else "false"
                continue
            if key == "tag_ids" and isinstance(value, list):
                import json
                data[key] = json.dumps(value)
                continue
            data[key] = value

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        if file_uploads:
            for field_name, filename, content in file_uploads:
                mime = _guess_mime(filename)
                files.append((field_name, (filename, content, mime)))

        return await self.post_multipart(
            "/api/warranties",
            data=data,
            files=files if files else None,
        )

    async def update_warranty(
        self,
        warranty_id: int,
        fields: dict[str, Any],
        file_uploads: list[tuple[str, str, bytes]] | None = None,
    ) -> Any:
        current = await self.get_warranty(warranty_id)
        if not current or "error" in current:
            return current

        data: dict[str, Any] = {}
        _ensure_required_put_fields(data, fields, current)

        for key, value in fields.items():
            if value is None:
                continue
            if key == "serial_numbers" and isinstance(value, list):
                for sn in value:
                    data.setdefault("serial_numbers[]", [])
                    if isinstance(data["serial_numbers[]"], list):
                        data["serial_numbers[]"].append(sn)
                continue
            if key == "is_lifetime":
                data[key] = "true" if value else "false"
                continue
            if key == "tag_ids" and isinstance(value, list):
                import json
                data[key] = json.dumps(value)
                continue
            data[key] = value

        files: list[tuple[str, tuple[str, bytes, str]]] = []
        if file_uploads:
            for field_name, filename, content in file_uploads:
                mime = _guess_mime(filename)
                files.append((field_name, (filename, content, mime)))

        return await self.put_multipart(
            f"/api/warranties/{warranty_id}",
            data=data,
            files=files if files else None,
        )

    async def upload_file_to_warranty(
        self,
        warranty_id: int,
        file_type: str,
        file_name: str,
        content: bytes,
    ) -> Any:
        current = await self.get_warranty(warranty_id)
        if not current or "error" in current:
            return current
        data: dict[str, Any] = {}
        _ensure_required_put_fields(data, {}, current)
        mime = _guess_mime(file_name)
        return await self.put_multipart(
            f"/api/warranties/{warranty_id}",
            data=data,
            files=[(file_type, (file_name, content, mime))],
        )

    async def download_and_upload(
        self,
        warranty_id: int,
        file_type: str,
        file_name: str,
        url: str,
    ) -> Any:
        async with httpx.AsyncClient(timeout=_UPLOAD_TIMEOUT) as c:
            r = await c.get(url)
            r.raise_for_status()
            content = r.content
        return await self.upload_file_to_warranty(warranty_id, file_type, file_name, content)

    async def list_tags(self) -> Any:
        return await self.get("/api/tags")

    async def create_tag(self, name: str, color: str | None = None) -> Any:
        data: dict[str, Any] = {"name": name}
        if color is not None:
            data["color"] = color
        return await self.post_json("/api/tags", data=data)

    async def list_currencies(self) -> Any:
        return await self.get("/api/currencies")


_DURATION_FIELDS = [
    "warranty_duration_years",
    "warranty_duration_months",
    "warranty_duration_days",
    "exact_expiration_date",
]


def _ensure_required_put_fields(
    data: dict[str, Any], fields: dict[str, Any], current: dict[str, Any]
) -> None:
    if "product_name" not in fields and current.get("product_name"):
        data["product_name"] = current["product_name"]
    if "purchase_date" not in fields and current.get("purchase_date"):
        data["purchase_date"] = current["purchase_date"]
    has_duration = any(
        k in fields
        for k in _DURATION_FIELDS + ["is_lifetime"]
    )
    if not has_duration:
        if current.get("is_lifetime"):
            data["is_lifetime"] = "true"
        else:
            for df in _DURATION_FIELDS:
                if current.get(df) is not None:
                    data[df] = current[df]
                    break


def _guess_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mimes = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return mimes.get(ext, "application/octet-stream")


def decode_b64(content_b64: str) -> bytes:
    return base64.b64decode(content_b64)
