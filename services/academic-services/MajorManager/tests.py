from django.test import TestCase

from rest_framework_simplejwt.tokens import AccessToken

from DeparmentManager.models import Department
from .models import Major


class MajorAPITests(TestCase):
    url = "/api/majors/"

    def authenticate(self, role=1):
        token = AccessToken()
        token["user_id"], token["role"] = "test-user", role
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def test_role_one_can_crud_major(self):
        department = Department.objects.create(code="CNTT", name="Information Technology")
        self.authenticate()
        response = self.client.post(self.url, {"code": "KTPM", "name": "Software Engineering", "department_id": department.id})
        self.assertEqual(response.status_code, 201)
        major_id = response.json()["id"]
        self.assertEqual(self.client.get(f"{self.url}{major_id}/").status_code, 200)
        self.assertEqual(self.client.delete(f"{self.url}{major_id}/").status_code, 204)

    def test_validation_and_permissions(self):
        self.authenticate()
        self.assertEqual(self.client.post(self.url, {"code": "KTPM", "name": "Software", "department_id": 999}).status_code, 400)
        self.authenticate(role=2)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {"code": "KTPM", "name": "Software", "department_id": 1}).status_code, 403)

    def test_unknown_major_is_not_found(self):
        self.authenticate()
        self.assertEqual(self.client.get(f"{self.url}999/").status_code, 404)
