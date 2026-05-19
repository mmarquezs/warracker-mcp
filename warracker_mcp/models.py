"""Pydantic models for Warracker API fields."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WarrantyCreate(BaseModel):
    product_name: str = Field(description="Product name")
    purchase_date: str = Field(description="Purchase date (YYYY-MM-DD)")
    warranty_duration_years: int | None = Field(default=None, description="Warranty duration in years")
    warranty_duration_months: int | None = Field(default=None, description="Warranty duration in months")
    warranty_duration_days: int | None = Field(default=None, description="Warranty duration in days")
    exact_expiration_date: str | None = Field(default=None, description="Exact expiration date (YYYY-MM-DD)")
    is_lifetime: bool | None = Field(default=None, description="Lifetime warranty flag")
    serial_numbers: list[str] | None = Field(default=None, description="Serial numbers")
    product_url: str | None = Field(default=None, description="URL to product page")
    notes: str | None = Field(default=None, description="Free text notes")
    vendor: str | None = Field(default=None, description="Seller/vendor name")
    warranty_type: str | None = Field(default=None, description="Warranty type")
    model_number: str | None = Field(default=None, description="Model number")
    purchase_price: float | None = Field(default=None, description="Purchase price (must be >= 0)")
    currency: str | None = Field(default=None, description="3-letter currency code (e.g. USD, EUR)")
    tag_ids: list[int] | None = Field(default=None, description="Tag IDs to associate")
    invoice_url: str | None = Field(default=None, description="External invoice URL")
    manual_url: str | None = Field(default=None, description="External manual URL")
    other_document_url: str | None = Field(default=None, description="External document URL")


class WarrantyUpdate(BaseModel):
    product_name: str | None = None
    purchase_date: str | None = None
    warranty_duration_years: int | None = None
    warranty_duration_months: int | None = None
    warranty_duration_days: int | None = None
    exact_expiration_date: str | None = None
    is_lifetime: bool | None = None
    serial_numbers: list[str] | None = None
    product_url: str | None = None
    notes: str | None = None
    vendor: str | None = None
    warranty_type: str | None = None
    model_number: str | None = None
    purchase_price: float | None = None
    currency: str | None = None
    tag_ids: list[int] | None = None
    invoice_url: str | None = None
    manual_url: str | None = None
    other_document_url: str | None = None


class TagCreate(BaseModel):
    name: str = Field(description="Tag name")
    color: str | None = Field(default=None, description="Tag color (hex code)")


class FileUpload(BaseModel):
    warranty_id: int = Field(description="Target warranty ID")
    file_type: Literal["invoice", "manual", "other_document", "product_photo"] = Field(
        description="Type of file to upload"
    )
    file_name: str = Field(description="Filename with extension (e.g. receipt.pdf)")
    file_content_b64: str | None = Field(default=None, description="Base64-encoded file content")
    file_url: str | None = Field(default=None, description="URL to download the file from")
