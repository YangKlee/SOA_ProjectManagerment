from django.test import TestCase

from rest_framework_simplejwt.tokens import AccessToken
from DeparmentManager.models import Department
from MajorManager.models import Major
from SubMajorManager.models import SubMajor


class StudentAPITests(TestCase):
    url = "/api/students/"

    def authenticate(self, role=1):
        token = AccessToken(); token["user_id"], token["role"] = "test-user", role
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def academic_data(self):
        department = Department.objects.create(code="CNTT", name="Information Technology")
        major = Major.objects.create(code="KTPM", name="Software Engineering", department=department)
        return major, SubMajor.objects.create(code="WEB", name="Web Development", major=major)

    def test_role_one_can_crud_student(self):
        major, sub_major = self.academic_data(); self.authenticate()
        payload = {"student_code": "SV001", "full_name": "Nguyen An", "email": "an@example.com", "major_id": major.id, "sub_major_id": sub_major.id}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201)
        student_id = response.json()["id"]
        self.assertEqual(self.client.patch(f"{self.url}{student_id}/", '{"phone": "0900000000"}', content_type="application/json").status_code, 200)
        self.assertEqual(self.client.delete(f"{self.url}{student_id}/").status_code, 204)

    def test_sub_major_must_match_major_and_read_is_public_to_authenticated_roles(self):
        major, _ = self.academic_data()
        other_department = Department.objects.create(code="KT", name="Economics")
        other_major = Major.objects.create(code="QTKD", name="Business", department=other_department)
        other_sub_major = SubMajor.objects.create(code="SALE", name="Sales", major=other_major)
        self.authenticate()
        payload = {"student_code": "SV001", "full_name": "Nguyen An", "email": "an@example.com", "major_id": major.id, "sub_major_id": other_sub_major.id}
        self.assertEqual(self.client.post(self.url, payload).status_code, 400)
        self.authenticate(2)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, payload).status_code, 403)

    def test_unauthenticated_and_missing_student(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.authenticate()
        self.assertEqual(self.client.get(f"{self.url}999/").status_code, 404)
