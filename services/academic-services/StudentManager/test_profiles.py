from unittest.mock import patch

from django.db import connection, IntegrityError
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from DeparmentManager.models import Department
from MajorManager.models import Major
from SubMajorManager.models import SubMajor
from LectureManager.models import Lecturer
from StudentManager.models import Student
from identity_management import IdentityFailure


class CompositeLifecycleTests(TransactionTestCase):
    """Temporary DB fixtures plus mocked published REST; no project DB or auth ORM."""
    models = [Department, Major, SubMajor, Student, Lecturer]

    def setUp(self):
        with connection.schema_editor() as editor:
            for model in self.models:
                editor.create_model(model)
        Department.objects.create(department_id="K1", name="Khoa")
        Major.objects.create(major_id="M1", name="Major", department_id="K1")
        self.client = APIClient()
        self.authorize()
        self.profiles = {}
        self.calls = []
        self.remote = patch("profile_management.identity_management.call", side_effect=self.identity)
        self.remote.start()
        self.addCleanup(self.remote.stop)

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS "ExternalReference"')
        with connection.schema_editor() as editor:
            for model in reversed(self.models):
                editor.delete_model(model)

    def authorize(self, role=1):
        token = AccessToken()
        token["user_id"] = "admin"
        token["role"] = role
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def identity(self, request, kind, method, pk, data, batch):
        self.assertFalse(connection.in_atomic_block, "HTTP must run outside SQLite write transactions")
        self.calls.append((kind, method, pk))
        if batch:
            return {key: self.profiles.get(key) for key in data["user_ids"]}
        if method == "POST":
            pk = data["user_id"]
            if pk in self.profiles:
                raise IdentityFailure(status=409)
            self.profiles[pk] = {key: value for key, value in data.items() if key != "password"}
            self.profiles[pk]["role"] = 3 if kind == "students" else 2
        elif pk not in self.profiles:
            raise IdentityFailure(status=404)
        elif method == "PATCH":
            self.profiles[pk].update({key: value for key, value in data.items() if key != "password"})
        elif method == "DELETE":
            del self.profiles[pk]
            return None
        return dict(self.profiles[pk])

    def payload(self, kind, pk):
        academic = {"student_id": pk, "major_id": "M1", "sub_major_id": None,
                    "accumulated_credits": 90, "gpa": 3.5} if kind == "students" else {"lecturer_id": pk, "department_id": "K1"}
        return {**academic, "user": {"email": f"{pk}@example.com", "phone": pk, "password": "secret", "first_name": "An"}}

    def create(self, kind="students", pk="SV01"):
        response = self.client.post(f"/api/v1/{kind}/", self.payload(kind, pk), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_both_composite_lifecycles_with_string_ids(self):
        for kind, model, pk in [("students", Student, "SV01"), ("lecturers", Lecturer, "GV01")]:
            self.create(kind, pk)
            base = f"/api/v1/{kind}/"
            self.assertEqual(self.client.get(base).data[0]["user"]["first_name"], "An")
            self.assertNotIn("password", str(self.client.get(base).data))
            response = self.client.patch(base + pk + "/", {"user": {"first_name": "Binh"}}, format="json")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["user"]["first_name"], "Binh")
            self.assertEqual(self.client.delete(base + pk + "/").status_code, 204)
            self.assertFalse(model.objects.filter(pk=pk).exists())
            self.assertNotIn(pk, self.profiles)

    def test_validation_and_duplicates_precede_remote_mutation(self):
        response = self.client.post("/api/v1/students/", {**self.payload("students", "SV"), "major_id": "missing"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.calls)
        for invalid in [{"student_id": ".."}, {"accumulated_credits": 2**63}, {"user": {"role": 1}}]:
            response = self.client.post("/api/v1/students/", {**self.payload("students", "SV"), **invalid}, format="json")
            self.assertEqual(response.status_code, 400)
        self.assertFalse(self.calls)
        self.create()
        self.calls.clear()
        self.assertEqual(self.client.post("/api/v1/students/", self.payload("students", "SV01"), format="json").status_code, 409)
        self.assertFalse(self.calls)
        self.assertEqual(self.client.patch("/api/v1/students/SV01/", {"student_id": "new"}, format="json").status_code, 400)

    def test_create_local_failure_compensates_identity(self):
        with patch.object(Student.objects, "create", side_effect=IntegrityError("private")):
            response = self.client.post("/api/v1/students/", self.payload("students", "SV01"), format="json")
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("SV01", self.profiles)
        self.assertEqual([method for _, method, _ in self.calls], ["POST", "DELETE"])

    def test_create_uncertain_write_never_replays_or_deletes(self):
        with patch("profile_management.identity_management.call", side_effect=IdentityFailure(uncertain=True)) as remote:
            response = self.client.post("/api/v1/students/", self.payload("students", "SV01"), format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "operation_incomplete")
        remote.assert_called_once()
        self.assertFalse(Student.objects.exists())

    def test_failed_create_compensation_reports_incomplete(self):
        with patch.object(Student.objects, "create", side_effect=IntegrityError("private")), \
             patch("profile_management.identity_management.call", side_effect=[{"user_id": "SV01"}, IdentityFailure()]):
            response = self.client.post("/api/v1/students/", self.payload("students", "SV01"), format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "operation_incomplete")

    def test_edit_confirmed_failure_restores_academic_values(self):
        self.create()
        original = self.identity
        def remote(*args):
            if args[2] == "PATCH":
                raise IdentityFailure(status=409)
            return original(*args)
        with patch("profile_management.identity_management.call", side_effect=remote):
            response = self.client.patch("/api/v1/students/SV01/", {"gpa": 3.9, "user": {"email": "duplicate@example.com"}}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Student.objects.get(pk="SV01").gpa, 3.5)

    def test_uncertain_edit_returns_incomplete_without_replay(self):
        self.create()
        with patch("profile_management.identity_management.call", side_effect=[self.profiles["SV01"], IdentityFailure(uncertain=True)]) as remote:
            response = self.client.patch("/api/v1/students/SV01/", {"gpa": 3.9, "user": {"first_name": "Binh"}}, format="json")
        self.assertEqual(response.data["code"], "operation_incomplete")
        self.assertEqual(remote.call_count, 2)

    def test_delete_auth_reference_restores_child(self):
        self.create("lecturers", "GV01")
        with patch("profile_management.identity_management.call", side_effect=[self.profiles["GV01"], IdentityFailure(status=409)]):
            response = self.client.delete("/api/v1/lecturers/GV01/")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Lecturer.objects.filter(pk="GV01").exists())

    def test_failed_delete_restoration_reports_incomplete(self):
        self.create("lecturers", "GV01")
        with patch.object(Lecturer.objects, "create", side_effect=IntegrityError("private")), \
             patch("profile_management.identity_management.call", side_effect=[self.profiles["GV01"], IdentityFailure(status=409)]):
            response = self.client.delete("/api/v1/lecturers/GV01/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "operation_incomplete")

    def test_academic_foreign_reference_prevents_identity_delete(self):
        self.create()
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE "ExternalReference" (id TEXT REFERENCES "Students" ("StudentId"))')
            cursor.execute('INSERT INTO "ExternalReference" VALUES (%s)', ["SV01"])
        self.calls.clear()
        response = self.client.delete("/api/v1/students/SV01/")
        self.assertEqual(response.status_code, 409)
        self.assertEqual([method for _, method, _ in self.calls], ["GET"])
        self.assertTrue(Student.objects.filter(pk="SV01").exists())

    def test_lost_delete_response_resolves_by_read_or_reports_incomplete(self):
        for pk, lookup, expected in [("one", IdentityFailure(status=404), 204), ("two", IdentityFailure(), 503)]:
            self.create("students", pk)
            with patch("profile_management.identity_management.call", side_effect=[self.profiles[pk], IdentityFailure(uncertain=True), lookup]) as remote:
                response = self.client.delete(f"/api/v1/students/{pk}/")
            self.assertEqual(response.status_code, expected)
            self.assertEqual(remote.call_count, 3)

    def test_confirmed_missing_identity_after_child_delete_is_complete(self):
        self.create()
        with patch("profile_management.identity_management.call", side_effect=[self.profiles["SV01"], IdentityFailure(status=404)]):
            response = self.client.delete("/api/v1/students/SV01/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Student.objects.exists())

    def test_all_profiles_require_admin_and_methods_are_bounded(self):
        for role in [2, 3]:
            self.authorize(role)
            for kind in ["students", "lecturers"]:
                self.assertEqual(self.client.get(f"/api/v1/{kind}/").status_code, 403)
                self.assertEqual(self.client.post(f"/api/v1/{kind}/", {}, format="json").status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.get("/api/v1/students/").status_code, 401)
        self.authorize()
        self.assertEqual(self.client.post("/api/v1/students/SV/", {}, format="json").status_code, 405)
        self.assertEqual(self.client.patch("/api/v1/students/", {}, format="json").status_code, 405)
        self.assertEqual(self.client.get("/api/v1/students/missing/").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/students/", {"padding": "x" * 65537}, format="json").status_code, 400)
