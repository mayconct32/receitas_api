import json
from http import HTTPStatus
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient


def unique_email(prefix: str = "chef") -> str:
    return f"{prefix}-{uuid4().hex[:8]}@email.com"


def build_chef_payload(
    *,
    chef_name: str | None = None,
    email: str | None = None,
    password: str = "password123",
) -> dict:
    return {
        "chef_name": chef_name or f"Alice-{uuid4().hex[:8]}",
        "email": email or unique_email("chef"),
        "password": password,
    }


def create_chef(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "password123",
    chef_name: str | None = None,
) -> dict:
    payload = build_chef_payload(
        chef_name=chef_name,
        email=email,
        password=password,
    )
    response = client.post(
        "/v1/chefs/",
        json=payload,
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return response.json()


def auth_headers(client: TestClient, *, email: str, password: str = "password123") -> dict[str, str]:
    response = client.post(
        "/v1/chefs/auth",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    token = response.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
    }


def create_authenticated_chef(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "password123",
    chef_name: str | None = None,
) -> tuple[dict, dict[str, str]]:
    created = create_chef(
        client,
        email=email,
        password=password,
        chef_name=chef_name,
    )
    headers = auth_headers(client, email=created["email"], password=password)
    return created, headers


