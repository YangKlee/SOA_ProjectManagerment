from django.test import TestCase

from rest_framework_simplejwt.tokens import AccessToken

from .models import Department


class DepartmentAPITests(TestCase):
    url = "/api/departments/"

    def token_for(self, role):
        token = AccessToken()
        token["user_id"] = "test-user"
        token["role"] = role
        return str(token)

    def authenticate(self, role=1):
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {self.token_for(role)}"

    def test_authenticated_users_can_list_departments(self):
        Department.objects.create(code="CNTT", name="Information Technology")
        self.authenticate(role=2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["code"], "CNTT")

    def test_role_one_can_create_and_update_department(self):
        self.authenticate()
        response = self.client.post(self.url, {"code": "KTPM", "name": "Software Engineering"})
        self.assertEqual(response.status_code, 201)
        department_id = response.json()["id"]
        response = self.client.patch(f"{self.url}{department_id}/", '{"name": "Software Engineering Updated"}', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Software Engineering Updated")

    def test_non_role_one_cannot_write(self):
        self.authenticate(role=2)
        response = self.client.post(self.url, {"code": "KT", "name": "Economics"})
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_and_unknown_resource_responses(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.authenticate()
        self.assertEqual(self.client.get(f"{self.url}999/").status_code, 404)

    def test_duplicate_code_is_rejected(self):
        Department.objects.create(code="CNTT", name="Information Technology")
        self.authenticate()
        response = self.client.post(self.url, {"code": "CNTT", "name": "Different name"})
        self.assertEqual(response.status_code, 400)
