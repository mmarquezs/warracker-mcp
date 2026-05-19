"""Warracker MCP server — exposes warranty management to AI agents.

Tools:
  - warranty_create       — create a warranty with all fields + optional files
  - warranty_update       — update warranty fields by ID
  - warranty_get          — get single warranty details
  - warranties_list       — list/search warranties
  - tags_list             — list existing tags
  - tag_create            — create a tag
  - currencies_list       — supported currencies
  - warranty_upload_file  — upload file to existing warranty (base64 or URL)
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from warracker_mcp.client import WarrackerClient, WarrackerError, decode_b64

mcp = FastMCP("Warracker")


def _client() -> WarrackerClient:
    return WarrackerClient()


def _clean(params: dict) -> dict:
    return {k: v for k, v in params.items() if v is not None}


def _fields_to_dict(fields: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        result[key] = value
    return result


def _parse_file_upload(
    file_content_b64: str | None = None,
    file_name: str | None = None,
    file_type: str | None = None,
) -> list[tuple[str, str, bytes]] | None:
    if not file_content_b64 or not file_name or not file_type:
        return None
    content = decode_b64(file_content_b64)
    return [(file_type, file_name, content)]


@mcp.tool
async def warranty_create(
    product_name: str,
    purchase_date: str,
    warranty_duration_years: int | None = None,
    warranty_duration_months: int | None = None,
    warranty_duration_days: int | None = None,
    exact_expiration_date: str | None = None,
    is_lifetime: bool | None = None,
    serial_numbers: list[str] | None = None,
    product_url: str | None = None,
    notes: str | None = None,
    vendor: str | None = None,
    warranty_type: str | None = None,
    model_number: str | None = None,
    purchase_price: float | None = None,
    currency: str | None = None,
    tag_ids: list[int] | None = None,
    invoice_url: str | None = None,
    manual_url: str | None = None,
    other_document_url: str | None = None,
    file_content_b64: str | None = None,
    file_name: str | None = None,
    file_type: str | None = None,
) -> dict:
    """Create a new warranty in Warracker.

    Required: product_name, purchase_date, and exactly one duration field
    (warranty_duration_years, warranty_duration_months, warranty_duration_days,
    exact_expiration_date, or is_lifetime=True).

    Optionally attach a file by providing file_content_b64 (base64-encoded),
    file_name (e.g. "receipt.pdf"), and file_type (invoice|manual|other_document|product_photo).
    """
    fields = _clean({
        "product_name": product_name,
        "purchase_date": purchase_date,
        "warranty_duration_years": warranty_duration_years,
        "warranty_duration_months": warranty_duration_months,
        "warranty_duration_days": warranty_duration_days,
        "exact_expiration_date": exact_expiration_date,
        "is_lifetime": is_lifetime,
        "serial_numbers": serial_numbers,
        "product_url": product_url,
        "notes": notes,
        "vendor": vendor,
        "warranty_type": warranty_type,
        "model_number": model_number,
        "purchase_price": purchase_price,
        "currency": currency,
        "tag_ids": tag_ids,
        "invoice_url": invoice_url,
        "manual_url": manual_url,
        "other_document_url": other_document_url,
    })

    file_uploads = _parse_file_upload(file_content_b64, file_name, file_type)
    return await _client().create_warranty(fields, file_uploads)


@mcp.tool
async def warranty_update(
    warranty_id: int,
    product_name: str | None = None,
    purchase_date: str | None = None,
    warranty_duration_years: int | None = None,
    warranty_duration_months: int | None = None,
    warranty_duration_days: int | None = None,
    exact_expiration_date: str | None = None,
    is_lifetime: bool | None = None,
    serial_numbers: list[str] | None = None,
    product_url: str | None = None,
    notes: str | None = None,
    vendor: str | None = None,
    warranty_type: str | None = None,
    model_number: str | None = None,
    purchase_price: float | None = None,
    currency: str | None = None,
    tag_ids: list[int] | None = None,
    invoice_url: str | None = None,
    manual_url: str | None = None,
    other_document_url: str | None = None,
    file_content_b64: str | None = None,
    file_name: str | None = None,
    file_type: str | None = None,
) -> dict:
    """Update an existing warranty by ID.

    Only provided fields are changed. Optionally attach a file by providing
    file_content_b64, file_name, and file_type.
    """
    fields = _clean({
        "product_name": product_name,
        "purchase_date": purchase_date,
        "warranty_duration_years": warranty_duration_years,
        "warranty_duration_months": warranty_duration_months,
        "warranty_duration_days": warranty_duration_days,
        "exact_expiration_date": exact_expiration_date,
        "is_lifetime": is_lifetime,
        "serial_numbers": serial_numbers,
        "product_url": product_url,
        "notes": notes,
        "vendor": vendor,
        "warranty_type": warranty_type,
        "model_number": model_number,
        "purchase_price": purchase_price,
        "currency": currency,
        "tag_ids": tag_ids,
        "invoice_url": invoice_url,
        "manual_url": manual_url,
        "other_document_url": other_document_url,
    })

    file_uploads = _parse_file_upload(file_content_b64, file_name, file_type)
    return await _client().update_warranty(warranty_id, fields, file_uploads)


@mcp.tool
async def warranty_get(warranty_id: int) -> dict:
    """Get a single warranty by its ID."""
    return await _client().get_warranty(warranty_id)


@mcp.tool
async def warranties_list(
    search: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict:
    """List or search warranties.

    Use `search` to filter by product name or notes.
    Use `page` and `per_page` for pagination.
    """
    params = _clean({"search": search, "page": page, "per_page": per_page})
    return await _client().list_warranties(params)


@mcp.tool
async def tags_list() -> list | dict:
    """List all existing tags in Warracker."""
    return await _client().list_tags()


@mcp.tool
async def tag_create(
    name: str,
    color: str | None = None,
) -> dict:
    """Create a new tag.

    Provide a `name` and optionally a `color` (hex code like #FF0000).
    """
    return await _client().create_tag(name, color)


@mcp.tool
async def currencies_list() -> list | dict:
    """List all supported currencies in Warracker."""
    return await _client().list_currencies()


@mcp.tool
async def warranty_upload_file(
    warranty_id: int,
    file_type: str,
    file_name: str,
    file_content_b64: str | None = None,
    file_url: str | None = None,
) -> dict:
    """Upload a file to an existing warranty.

    Provide exactly one of:
      - file_content_b64: base64-encoded file content
      - file_url: URL to download the file from

    Also provide:
      - warranty_id: target warranty ID
      - file_type: one of invoice, manual, other_document, product_photo
      - file_name: filename with extension (e.g. "receipt.pdf")
    """
    client = _client()

    if file_content_b64 and file_url:
        return {"error": "Provide exactly one of file_content_b64 or file_url, not both"}

    if file_content_b64:
        content = decode_b64(file_content_b64)
        return await client.upload_file_to_warranty(warranty_id, file_type, file_name, content)

    if file_url:
        return await client.download_and_upload(warranty_id, file_type, file_name, file_url)

    return {"error": "Provide either file_content_b64 or file_url"}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
