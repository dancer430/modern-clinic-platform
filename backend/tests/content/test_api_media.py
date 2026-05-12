from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _png_bytes(size_kb: int = 1) -> bytes:
    img = Image.new("RGB", (8, 8), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()
    if size_kb > 1:
        payload = payload + b"\0" * (size_kb * 1024 - len(payload))
    return payload


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.mark.django_db
def test_upload_rejects_non_image(admin_client):
    f = SimpleUploadedFile("x.txt", b"hello", content_type="text/plain")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_rejects_oversize(admin_client, settings):
    settings.MEDIA_UPLOAD_MAX_BYTES = 1024
    f = SimpleUploadedFile("big.png", _png_bytes(size_kb=2), content_type="image/png")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_returns_url(admin_client):
    f = SimpleUploadedFile("ok.png", _png_bytes(), content_type="image/png")
    resp = admin_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 201, resp.content
    assert "url" in resp.json()


@pytest.mark.django_db
def test_upload_requires_admin_or_doctor(api_client, patient_user):
    api_client.force_authenticate(user=patient_user)
    f = SimpleUploadedFile("ok.png", _png_bytes(), content_type="image/png")
    resp = api_client.post("/api/media/upload/", {"file": f}, format="multipart")
    assert resp.status_code == 403
