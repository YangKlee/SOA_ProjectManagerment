from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from . import services
from .models import Student
from .serializers import StudentRequestDTO


class StudentServiceTests(SimpleTestCase):
    data = {'student_id': '1', 'major_id': '2', 'sub_major_id': '3', 'accumulated_credits': 90, 'gpa': 3.5}

    def test_mapping_and_dto(self):
        self.assertFalse(Student._meta.managed)
        self.assertEqual(Student._meta.db_table, 'Students')
        self.assertTrue(StudentRequestDTO(data=self.data).is_valid())

    def test_list_and_get(self):
        with patch.object(Student.objects, "all") as operation:
            self.assertIs(services.list_students(), operation.return_value)
        with patch.object(Student.objects, "get") as operation:
            self.assertIs(services.get_student("1"), operation.return_value)
            operation.assert_called_once_with(pk="1")

    def test_create_with_valid_relationship(self):
        with patch.object(services.Major.objects, "filter") as parent, \
             patch.object(Student.objects, "create") as create:
            parent.return_value.exists.return_value = True
            with patch.object(services.SubMajor.objects, "filter") as child:
                child.return_value.exists.return_value = True
                self.assertIs(services.create_student(self.data), create.return_value)
                child.assert_called_once_with(pk="3", major_id="2")
            parent.assert_called_once_with(pk="2")
            create.assert_called_once_with(**self.data)

    def test_invalid_parent_prevents_create_and_update(self):
        obj = Student(**self.data)
        obj.save = Mock()
        with patch.object(services.Major.objects, "filter") as parent, \
             patch.object(Student.objects, "create") as create, \
             patch.object(Student.objects, "get", return_value=obj):
            parent.return_value.exists.return_value = False
            for operation in [lambda: services.create_student(self.data),
                              lambda: services.update_student("1", {'major_id': "missing"})]:
                with self.assertRaises(services.BusinessValidationError) as caught:
                    operation()
                self.assertIn('major_id', caught.exception.errors)
            create.assert_not_called()
            obj.save.assert_not_called()

    def test_partial_update_preserves_unsupplied_fields(self):
        obj = Student(**self.data)
        obj.save = Mock()
        with patch.object(Student.objects, "get", return_value=obj), \
             patch.object(services, "_validate") as validate:
            self.assertIs(services.update_student("1", {'gpa': 3.8}), obj)
            self.assertEqual(getattr(obj, 'student_id'), "1")
            self.assertEqual(getattr(obj, 'gpa'), 3.8)
            obj.save.assert_called_once_with()
            self.assertEqual(validate.call_count, 1)

    def test_delete_and_missing_records(self):
        with patch.object(Student.objects, "get") as get:
            services.delete_student("1")
            get.assert_called_once_with(pk="1")
            get.return_value.delete.assert_called_once_with()
        with patch.object(Student.objects, "get", side_effect=Student.DoesNotExist):
            for operation in [lambda: services.get_student("missing"),
                              lambda: services.update_student("missing", {}),
                              lambda: services.delete_student("missing")]:
                with self.assertRaises(Student.DoesNotExist):
                    operation()


class StudentEndpointTests(SimpleTestCase):
    collection = "/api/students/"
    detail = "/api/students/1/"
    data = {'student_id': '1', 'major_id': '2', 'sub_major_id': '3', 'accumulated_credits': 90, 'gpa': 3.5}

    def setUp(self):
        self.client = APIClient()
        self.authenticate(1)
        self.obj = SimpleNamespace(**self.data)

    def authenticate(self, role):
        token = AccessToken()
        token["user_id"] = "test-user"
        token["role"] = role
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def request(self, method, path, data=None):
        return getattr(self.client, method)(path, data=data, format="json")

    def test_crud_delegation_and_responses(self):
        cases = [
            ("get", self.collection, None, "list_students", (), [self.obj], 200, [self.data]),
            ("post", self.collection, self.data, "create_student", (self.data,), self.obj, 201, self.data),
            ("get", self.detail, None, "get_student", (1,), self.obj, 200, self.data),
            ("put", self.detail, self.data, "update_student", (1, self.data), self.obj, 200, self.data),
            ("patch", self.detail, {'gpa': 3.8}, "update_student", (1, {'gpa': 3.8}), self.obj, 200, self.data),
            ("delete", self.detail, None, "delete_student", (1,), None, 204, None),
        ]
        for method, path, payload, name, args, result, status, expected in cases:
            with self.subTest(method=method, path=path), patch.object(services, name, return_value=result) as operation:
                response = self.request(method, path, payload)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.data, expected)
                operation.assert_called_once_with(*args)
                if status == 204:
                    self.assertEqual(response.content, b"")

    def test_dto_validation_before_service(self):
        for method, path, name, data in [
            ("post", self.collection, "create_student", {}),
            ("put", self.detail, "update_student", {}),
            ("patch", self.detail, "update_student", {'student_id': ""}),
        ]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, data).status_code, 400)
                operation.assert_not_called()

    def test_business_validation_returns_field_errors(self):
        for method, path, name in [("post", self.collection, "create_student"),
                                   ("put", self.detail, "update_student"),
                                   ("patch", self.detail, "update_student")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=services.BusinessValidationError({'major_id': "Invalid relation."})):
                response = self.request(method, path, self.data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(str(response.data['major_id']), "Invalid relation.")

    def test_missing_records_return_404(self):
        for method, name in [("get", "get_student"), ("put", "update_student"),
                             ("patch", "update_student"), ("delete", "delete_student")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=Student.DoesNotExist):
                self.assertEqual(self.request(method, self.detail, self.data).status_code, 404)

    def test_unauthenticated_requests(self):
        self.client.credentials()
        for method, path in [("get", self.collection), ("post", self.collection),
                             ("get", self.detail), ("put", self.detail),
                             ("patch", self.detail), ("delete", self.detail)]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.request(method, path, self.data).status_code, 401)

    def test_invalid_and_expired_tokens(self):
        token = AccessToken()
        token["user_id"] = "test-user"
        token.set_exp(lifetime=timedelta(seconds=-10))
        for value in ["invalid-token", str(token)]:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {value}")
            self.assertEqual(self.client.get(self.collection).status_code, 401)

    def test_non_admin_write_denied_before_service(self):
        self.authenticate(2)
        for method, path, name in [("post", self.collection, "create_student"),
                                   ("put", self.detail, "update_student"),
                                   ("patch", self.detail, "update_student"),
                                   ("delete", self.detail, "delete_student")]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, self.data).status_code, 403)
                operation.assert_not_called()

    def test_non_admin_reads(self):
        self.authenticate(2)
        with patch.object(services, "list_students", return_value=[self.obj]):
            self.assertEqual(self.client.get(self.collection).status_code, 200)
        with patch.object(services, "get_student", return_value=self.obj):
            self.assertEqual(self.client.get(self.detail).status_code, 200)

    @patch.object(services, "create_student")
    def test_detail_post_returns_405(self, operation):
        self.assertEqual(self.request("post", self.detail, self.data).status_code, 405)
        operation.assert_not_called()

class StudentRelationshipTests(SimpleTestCase):
    def setUp(self):
        self.obj = Student(student_id="1", major_id="2", sub_major_id="3",
                           accumulated_credits=90, gpa=3.5)
        self.obj.save = Mock()

    def test_gpa_patch_validates_existing_relationship(self):
        with patch.object(Student.objects, "get", return_value=self.obj), \
             patch.object(services.Major.objects, "filter") as major, \
             patch.object(services.SubMajor.objects, "filter") as sub_major:
            major.return_value.exists.return_value = True
            sub_major.return_value.exists.return_value = True
            services.update_student("1", {"gpa": 3.8})
            major.assert_called_once_with(pk="2")
            sub_major.assert_called_once_with(pk="3", major_id="2")
            self.obj.save.assert_called_once_with()

    def test_changing_major_rejects_existing_incompatible_sub_major(self):
        with patch.object(Student.objects, "get", return_value=self.obj), \
             patch.object(services.Major.objects, "filter") as major, \
             patch.object(services.SubMajor.objects, "filter") as sub_major:
            major.return_value.exists.return_value = True
            sub_major.return_value.exists.return_value = False
            with self.assertRaises(services.BusinessValidationError) as caught:
                services.update_student("1", {"major_id": "4"})
            self.assertIn("sub_major_id", caught.exception.errors)
            sub_major.assert_called_once_with(pk="3", major_id="4")
            self.assertEqual(self.obj.major_id, "2")
            self.obj.save.assert_not_called()

    def test_explicit_null_clears_sub_major(self):
        with patch.object(Student.objects, "get", return_value=self.obj), \
             patch.object(services.Major.objects, "filter") as major, \
             patch.object(services.SubMajor.objects, "filter") as sub_major:
            major.return_value.exists.return_value = True
            services.update_student("1", {"sub_major_id": None})
            self.assertIsNone(self.obj.sub_major_id)
            sub_major.assert_not_called()
            self.obj.save.assert_called_once_with()

    def test_create_rejects_incompatible_sub_major_before_persistence(self):
        with patch.object(services.Major.objects, "filter") as major, \
             patch.object(services.SubMajor.objects, "filter") as sub_major, \
             patch.object(Student.objects, "create") as create:
            major.return_value.exists.return_value = True
            sub_major.return_value.exists.return_value = False
            with self.assertRaises(services.BusinessValidationError) as caught:
                services.create_student({"student_id": "1", "major_id": "2",
                                         "sub_major_id": "3", "accumulated_credits": 90,
                                         "gpa": 3.5})
            self.assertIn("sub_major_id", caught.exception.errors)
            create.assert_not_called()
