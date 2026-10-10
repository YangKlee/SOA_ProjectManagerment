from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Users
from .identities import IdentityThrottle


@override_settings(INTERNAL_SERVICE_TOKEN="test-identity-secret")
class IdentityLifecycleTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        with connection.schema_editor() as editor:
            editor.create_model(Users)
        self.admin = Users.objects.create(userid="admin", email="admin@example.com", phone="admin",
                                          password="admin-password", role=1)
        self.client = APIClient()
        self.authorize()

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS "ExternalReference"')
        with connection.schema_editor() as editor:
            editor.delete_model(Users)

    def authorize(self, role=1, service="test-identity-secret"):
        token = AccessToken()
        token["user_id"] = "admin"
        token["role"] = role
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SERVICE_TOKEN=service)

    def payload(self, pk="SV01"):
        return {"user_id": pk, "last_name": "Nguyen", "first_name": "An", "gender": None,
                "date_of_birth": "2001-02-03", "email": f"{pk}@example.com", "phone": pk,
                "status": 1, "password": "  mật-khẩu  "}

    def test_both_roles_lifecycle_and_existing_login_contract(self):
        for kind, role in [("students", 3), ("lecturers", 2)]:
            with self.subTest(kind=kind):
                payload = self.payload(kind)
                base = f"/internal/v1/identities/{kind}/"
                response = self.client.post(base, payload, format="json")
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data["role"], role)
                self.assertNotIn("password", response.data)
                self.assertTrue(response.data["created_at"])
                pk = payload["user_id"]
                self.assertEqual(Users.objects.get(pk=pk).password, payload["password"])
                response = self.client.patch(base + pk + "/", {"password": "new-password"}, format="json")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("password", response.data)
                response = self.client.patch(base + pk + "/", {"first_name": "Binh"}, format="json")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["first_name"], "Binh")
                self.assertEqual(Users.objects.get(pk=pk).password, "new-password")
                response = self.client.post(f"/internal/v1/identity-profiles/{kind}/",
                    {"user_ids": [pk, "missing", "admin"]}, format="json")
                self.assertIsNone(response.data["users"]["admin"])
                self.assertIsNone(response.data["users"]["missing"])
                self.assertNotIn("password", str(response.data))
                login = APIClient().post("/login/", {"userid": pk, "password": "new-password"}, format="json")
                self.assertEqual(login.status_code, 200, login.data)
                self.assertEqual(self.client.delete(base + pk + "/").status_code, 204)
                self.assertFalse(Users.objects.filter(pk=pk).exists())

    def test_unique_fields_and_validation_never_mutate_existing_user(self):
        base = "/internal/v1/identities/students/"
        self.assertEqual(self.client.post(base, self.payload(), format="json").status_code, 201)
        for changed in [{}, {"user_id": "other"}, {"user_id": "other", "email": "other@example.com"}]:
            response = self.client.post(base, {**self.payload(), **changed}, format="json")
            self.assertEqual(response.status_code, 409)
        for changed in [{"date_of_birth": "2026-02-30"}, {"role": 1}, {"password": ""}, {"email": "bad"},
                        {"gender": 2**63}, {"status": -(2**63)-1}, {"user_id": "../bad"}]:
            response = self.client.post(base, {**self.payload("new"), **changed}, format="json")
            self.assertEqual(response.status_code, 400)
        for payload in [{"user_id": "changed"}, {"role": 1}, {"created_at": "bad"}]:
            self.assertEqual(self.client.patch(base + "SV01/", payload, format="json").status_code, 400)
        self.assertEqual(Users.objects.get(pk="SV01").role, 3)

    def test_service_token_and_current_admin_and_token_role_required(self):
        base = "/internal/v1/identities/students/"
        for role, secret in [(1, ""), (1, "wrong"), (2, "test-identity-secret")]:
            self.authorize(role, secret)
            self.assertEqual(self.client.post(base, self.payload(), format="json").status_code, 403)
        self.authorize()
        Users.objects.filter(pk="admin").update(role=2)
        self.assertEqual(self.client.post(base, self.payload(), format="json").status_code, 403)
        self.client.credentials(HTTP_X_SERVICE_TOKEN="test-identity-secret")
        self.assertEqual(self.client.post(base, self.payload(), format="json").status_code, 401)
        self.assertFalse(Users.objects.filter(pk="SV01").exists())

    def test_wrong_role_self_and_external_fk_protected(self):
        self.client.post("/internal/v1/identities/students/", self.payload(), format="json")
        for pk in ["admin", "SV01"]:
            self.assertEqual(self.client.delete(f"/internal/v1/identities/lecturers/{pk}/").status_code, 403)
        # Synthetic external-owned reference fixture; application code never queries that table.
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE "ExternalReference" (id TEXT REFERENCES "Users" ("UserId"))')
            cursor.execute('INSERT INTO "ExternalReference" VALUES (%s)', ["SV01"])
        response = self.client.delete("/internal/v1/identities/students/SV01/")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Users.objects.filter(pk="SV01").exists())

    def test_batch_bounds_missing_and_wrong_method(self):
        self.assertEqual(self.client.get("/internal/v1/identities/students/missing/").status_code, 404)
        self.assertEqual(self.client.get("/internal/v1/identities/students/").status_code, 405)
        self.assertEqual(self.client.post("/internal/v1/identities/students/missing/", {}, format="json").status_code, 405)
        for data in [{"user_ids": ["x"] * 101}, {"user_ids": [], "password": True}, {"user_ids": ["x" * 65537]}]:
            self.assertEqual(self.client.post("/internal/v1/identity-profiles/students/", data, format="json").status_code, 400)

    def test_management_quota(self):
        with patch.object(IdentityThrottle, "rate", "1/min"):
            self.assertEqual(self.client.post("/internal/v1/identity-profiles/students/", {"user_ids": []}, format="json").status_code, 200)
            self.assertEqual(self.client.post("/internal/v1/identity-profiles/students/", {"user_ids": []}, format="json").status_code, 429)

    def test_one_internal_credential_works_for_both_capabilities(self):
        names = self.client.post("/internal/v1/user-display-names/", {"user_ids": []}, format="json")
        self.assertEqual(names.status_code, 200)
        identity = self.client.post("/internal/v1/identities/students/", self.payload(), format="json")
        self.assertEqual(identity.status_code, 201)
        self.authorize(service="wrong")
        self.assertEqual(self.client.post("/internal/v1/user-display-names/", {"user_ids": []}, format="json").status_code, 403)
        self.assertEqual(self.client.get("/internal/v1/identities/students/SV01/").status_code, 403)
