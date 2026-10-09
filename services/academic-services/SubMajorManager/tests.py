from django.test import TestCase

from rest_framework_simplejwt.tokens import AccessToken
from DeparmentManager.models import Department
from MajorManager.models import Major


class SubMajorAPITests(TestCase):
    url = "/api/sub-majors/"

    def authenticate(self, role=1):
        token = AccessToken(); token["user_id"], token["role"] = "test-user", role
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def test_crud_and_role_permission(self):
        department = Department.objects.create(code="CNTT", name="Information Technology")
        major = Major.objects.create(code="KTPM", name="Software Engineering", department=department)
        self.authenticate()
        response = self.client.post(self.url, {"code": "WEB", "name": "Web Development", "major_id": major.id})
        self.assertEqual(response.status_code, 201)
        obj_id = response.json()["id"]
        self.assertEqual(self.client.patch(f"{self.url}{obj_id}/", '{"name": "Web Engineering"}', content_type="application/json").status_code, 200)
        self.authenticate(2)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.delete(f"{self.url}{obj_id}/").status_code, 403)

    def test_invalid_major_and_missing_resource(self):
        self.authenticate()
        self.assertEqual(self.client.post(self.url, {"code": "WEB", "name": "Web", "major_id": 999}).status_code, 400)
        self.assertEqual(self.client.get(f"{self.url}999/").status_code, 404)
