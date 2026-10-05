from http import HTTPStatus
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jwt import decode

from server.tests.helpers import (
    auth_headers,
    build_chef_payload,
    create_authenticated_chef,
    create_chef,
    unique_email,
)


class TestChefEndpoints:
    def test_create_chef_returns_created_record(self, client: TestClient):
        email = unique_email("chef-create")
        payload = build_chef_payload(
            chef_name=f"Alice-{uuid4().hex[:8]}",
            email=email,
        )

        response = client.post("/v1/chefs/", json=payload)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()["email"] == email

    def test_list_chefs_returns_records(self, client: TestClient):
        email = unique_email("chef-list")
        create_chef(client, email=email)

        response = client.get("/v1/chefs/?offset=0&limit=10")

        assert response.status_code == HTTPStatus.OK
        assert any(item["email"] == email for item in response.json())

    def test_get_chef_by_id_returns_record(self, client: TestClient):
        created = create_chef(client, email=unique_email("chef-get"))

        response = client.get(f"/v1/chefs/{created['chef_id']}")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_id"] == created["chef_id"]

    def test_get_chef_by_id_returns_not_found_for_missing_record(self, client: TestClient):
        response = client.get("/v1/chefs/chef-does-not-exist")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "Chefs not found!"

    @pytest.mark.parametrize(
        ("password", "expected_detail"),
        [
            ("", "Field required"),
            ("wrong_password", "Incorrect username or password!"),
        ],
    )
    def test_auth_policy_variants(
        self,
        client: TestClient,
        password: str,
        expected_detail: str,
    ):
        email = unique_email("chef-auth-policy")
        create_chef(client, email=email)

        data = {"username": email, "password": password}
        if password == "":
            data = {"username": email}

        response = client.post("/v1/chefs/auth", data=data)

        if password == "":
            assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
            assert "password" in response.json()["detail"][0]["loc"]
        else:
            assert response.status_code == HTTPStatus.FORBIDDEN
            assert response.json()["detail"] == expected_detail

    def test_auth_chef_returns_token(self, client: TestClient):
        email = unique_email("chef-auth")
        create_chef(client, email=email)

        response = client.post(
            "/v1/chefs/auth",
            data={
                "username": email,
                "password": "password123",
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]

    def test_duplicate_email_returns_conflict(self, client: TestClient):
        email = unique_email("chef-conflict")
        create_chef(client, email=email)

        response = client.post(
            "/v1/chefs/",
            json={
                "chef_name": f"Another person-{uuid4().hex[:8]}",
                "email": email,
                "password": "password123",
            },
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()["detail"] == "This email already exists!"

    def test_get_me_returns_current_chef(self, client: TestClient):
        email = unique_email("chef-me")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.get("/v1/chefs/me", headers=headers)

        assert response.status_code == HTTPStatus.OK
        assert response.json()["email"] == created["email"]

    def test_get_me_requires_authentication(self, client: TestClient):
        response = client.get("/v1/chefs/me")

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]

    def test_deleted_chef_token_is_rejected(self, client: TestClient):
        email = unique_email("chef-ghost")
        created, headers = create_authenticated_chef(client, email=email)

        me = client.get("/v1/chefs/me", headers=headers)
        assert me.status_code == HTTPStatus.OK

        deleted = client.delete(
            f"/v1/chefs/{created['chef_id']}", headers=headers
        )
        assert deleted.status_code == HTTPStatus.OK

        response = client.get("/v1/chefs/me", headers=headers)

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_access_token_contains_chef_id_for_current_user_validation(self, client: TestClient):
        email = unique_email("chef-token-id")
        created, headers = create_authenticated_chef(client, email=email)
        token = headers["Authorization"].split(" ", 1)[1]
        payload = decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )

        assert payload["sub"] == email
        assert payload["chef_id"] == created["chef_id"]

    def test_create_chef_missing_required_fields_returns_422(self, client: TestClient):
        response = client.post(
            "/v1/chefs/",
            json={
                "chef_name": "Alice",
            },
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "email" in response.json()["detail"][0]["loc"]

    def test_list_chefs_returns_not_found_when_empty(self, client: TestClient):
        response = client.get("/v1/chefs/?offset=0&limit=10")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "Chefs not found!"

    def test_update_chef_returns_updated_record(self, client: TestClient):
        email = unique_email("chef-update")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={
                "chef_name": "Updated Alice",
                "email": unique_email("updated-email"),
                "password": "new-password",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_name"] == "Updated Alice"
        assert response.json()["email"] != email
        assert "access_token" not in response.json()

    def test_update_chef_with_unchanged_credentials_does_not_conflict(self, client: TestClient):
        email = unique_email("chef-update-same")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={
                "chef_name": created["chef_name"],
                "email": created["email"],
                "password": "new-password",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_name"] == created["chef_name"]
        assert response.json()["email"] == created["email"]

    def test_update_chef_with_other_chef_credentials_returns_conflict(self, client: TestClient):
        owner_email = unique_email("chef-owner-update-conflict")
        created, headers = create_authenticated_chef(client, email=owner_email)
        other = create_chef(client, email=unique_email("chef-other-conflict"))

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={
                "chef_name": other["chef_name"],
                "email": created["email"],
                "password": "new-password",
            },
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()["detail"] == "This name already exists!"

    def test_token_remains_valid_after_chef_update(self, client: TestClient):
        email = unique_email("chef-token-after-update")
        created, headers = create_authenticated_chef(client, email=email)

        new_email = unique_email("renamed-email")
        updated = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={
                "chef_name": "Renamed Alice",
                "email": new_email,
                "password": "new-password",
            },
        )
        assert updated.status_code == HTTPStatus.OK

        response = client.get("/v1/chefs/me", headers=headers)

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_id"] == created["chef_id"]
        assert response.json()["chef_name"] == "Renamed Alice"
        assert response.json()["email"] == new_email

    def test_delete_chef_removes_chef(self, client: TestClient):
        email = unique_email("chef-delete")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.delete(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["message"] == "Chef successfully excluded"

    def test_duplicate_chef_name_returns_conflict(self, client: TestClient):
        chef_name = f"Duplicate Chef-{uuid4().hex[:8]}"
        create_chef(client, email=unique_email("chef-name-1"), chef_name=chef_name)

        response = client.post(
            "/v1/chefs/",
            json={
                "chef_name": chef_name,
                "email": unique_email("chef-name-2"),
                "password": "password123",
            },
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()["detail"] == "This name already exists!"

    def test_delete_chef_requires_owner(self, client: TestClient):
        owner_email = unique_email("chef-owner")
        other_email = unique_email("chef-other")
        create_chef(client, email=owner_email)
        other = create_chef(client, email=other_email)
        headers = auth_headers(client, email=owner_email)

        response = client.delete(
            f"/v1/chefs/{other['chef_id']}",
            headers=headers,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()["detail"] == "unauthorized request"

    def test_update_chef_requires_owner(self, client: TestClient):
        owner_email = unique_email("chef-owner-update")
        other_email = unique_email("chef-other-update")
        create_chef(client, email=owner_email)
        other = create_chef(client, email=other_email)
        headers = auth_headers(client, email=owner_email)

        response = client.put(
            f"/v1/chefs/{other['chef_id']}",
            headers=headers,
            json={
                "chef_name": "Updated Alice",
                "email": unique_email("updated-email"),
                "password": "new-password",
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()["detail"] == "unauthorized request"

    def test_update_chef_allows_self_unchanged_name_and_email_with_password_change(self, client: TestClient):
        email = unique_email("chef-self-update")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={
                "chef_name": created["chef_name"],
                "email": created["email"],
                "password": "new-password",
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_name"] == created["chef_name"]
        assert response.json()["email"] == created["email"]

        reauth = client.post(
            "/v1/chefs/auth",
            data={"username": email, "password": "new-password"},
        )
        assert reauth.status_code == HTTPStatus.CREATED

    def test_update_chef_only_password_keeps_other_fields(self, client: TestClient):
        email = unique_email("chef-partial-update")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={"password": "new-password"},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_name"] == created["chef_name"]
        assert response.json()["email"] == created["email"]

        reauth = client.post(
            "/v1/chefs/auth",
            data={"username": email, "password": "new-password"},
        )
        assert reauth.status_code == HTTPStatus.CREATED

    def test_update_chef_only_name_keeps_email_and_password(self, client: TestClient):
        email = unique_email("chef-rename-only")
        created, headers = create_authenticated_chef(client, email=email)

        response = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={"chef_name": "Renamed Only"},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["chef_name"] == "Renamed Only"
        assert response.json()["email"] == email

        reauth = client.post(
            "/v1/chefs/auth",
            data={"username": email, "password": "password123"},
        )
        assert reauth.status_code == HTTPStatus.CREATED

    def test_update_chef_does_not_return_access_token(self, client: TestClient):
        email = unique_email("chef-fresh-token")
        created, headers = create_authenticated_chef(client, email=email)
        new_email = unique_email("fresh-token-email")

        updated = client.put(
            f"/v1/chefs/{created['chef_id']}",
            headers=headers,
            json={"email": new_email},
        )
        assert updated.status_code == HTTPStatus.OK
        assert "access_token" not in updated.json()

        me = client.get(
            "/v1/chefs/me",
            headers=headers,
        )
        assert me.status_code == HTTPStatus.OK
        assert me.json()["email"] == new_email
