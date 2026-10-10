from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.db import IntegrityError
from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from . import services
from .models import Lecturer
from .serializers import LecturerRequestDTO


class LecturerEndpointTests(SimpleTestCase):
    collection = "/api/lecturers/"
    detail = "/api/lecturers/GV001/"
    data = {'lecturer_id': 'GV001', 'department_id': '2'}

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
            ("get", self.collection, None, "list_lecturers", (), [self.obj], 200, [self.data]),
            ("post", self.collection, self.data, "create_lecturer", (self.data,), self.obj, 201, self.data),
            ("get", self.detail, None, "get_lecturer", ("GV001",), self.obj, 200, self.data),
            ("put", self.detail, self.data, "update_lecturer", ("GV001", self.data), self.obj, 200, self.data),
            ("patch", self.detail, {'department_id': None}, "update_lecturer", ("GV001", {'department_id': None}), self.obj, 200, self.data),
            ("delete", self.detail, None, "delete_lecturer", ("GV001",), None, 204, None),
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
            ("post", self.collection, "create_lecturer", {}),
            ("put", self.detail, "update_lecturer", {}),
            ("patch", self.detail, "update_lecturer", {'lecturer_id': ""}),
        ]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, data).status_code, 400)
                operation.assert_not_called()

    def test_business_validation_returns_field_errors(self):
        for method, path, name in [("post", self.collection, "create_lecturer"),
                                   ("put", self.detail, "update_lecturer"),
                                   ("patch", self.detail, "update_lecturer")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=services.BusinessValidationError({'department_id': "Invalid relation."})):
                response = self.request(method, path, self.data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(str(response.data['department_id']), "Invalid relation.")

    def test_missing_records_return_404(self):
        for method, name in [("get", "get_lecturer"), ("put", "update_lecturer"),
                             ("patch", "update_lecturer"), ("delete", "delete_lecturer")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=Lecturer.DoesNotExist):
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
        for method, path, name in [("post", self.collection, "create_lecturer"),
                                   ("put", self.detail, "update_lecturer"),
                                   ("patch", self.detail, "update_lecturer"),
                                   ("delete", self.detail, "delete_lecturer")]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, self.data).status_code, 403)
                operation.assert_not_called()

    def test_non_admin_reads(self):
        self.authenticate(2)
        with patch.object(services, "list_lecturers", return_value=[self.obj]):
            self.assertEqual(self.client.get(self.collection).status_code, 200)
        with patch.object(services, "get_lecturer", return_value=self.obj):
            self.assertEqual(self.client.get(self.detail).status_code, 200)

    @patch.object(services, "create_lecturer")
    def test_detail_post_returns_405(self, operation):
        self.assertEqual(self.request("post", self.detail, self.data).status_code, 405)
        operation.assert_not_called()



class LecturerServiceTests(SimpleTestCase):
    def setUp(self):
        self.data = {"lecturer_id": "GV001", "department_id": "F01"}
        self.obj = Lecturer(**self.data)
        self.obj.save = Mock()
        self.obj.delete = Mock()
        self.atomic = patch.object(services.transaction, "atomic").start()
        self.addCleanup(patch.stopall)
        self.get = patch.object(Lecturer.objects, "get", return_value=self.obj).start()
        self.parent = patch.object(services.Department.objects, "filter").start()
        self.parent.return_value.exists.return_value = True
        self.existing = patch.object(Lecturer.objects, "filter").start()
        self.existing.return_value.exists.return_value = False
        self.create = patch.object(Lecturer.objects, "create", return_value=self.obj).start()

    def test_mapping_and_relationship_metadata(self):
        self.assertFalse(Lecturer._meta.managed)
        self.assertEqual(Lecturer._meta.db_table, "Lecturers")
        self.assertEqual(Lecturer._meta.pk.column, "LecturerId")
        self.assertEqual(Lecturer._meta.pk.name, "lecturer_id")
        field = Lecturer._meta.get_field("department")
        self.assertEqual(field.column, "FacultyId")
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.model, services.Department)
        self.assertEqual({field.name for field in Lecturer._meta.fields}, {"lecturer_id", "department"})

    def test_dto_types_required_fields_and_safe_response(self):
        from .serializers import LecturerResponseDTO
        self.assertTrue(LecturerRequestDTO(data=self.data).is_valid())
        self.assertTrue(LecturerRequestDTO(data={"lecturer_id": "GV001"}).is_valid())
        self.assertTrue(LecturerRequestDTO(data={"department_id": None}, partial=True).is_valid())
        for data in [{}, {"lecturer_id": ""}, {"lecturer_id": "GV001", "department_id": ""}]:
            self.assertFalse(LecturerRequestDTO(data=data).is_valid())
        self.obj.password = "must-not-be-exposed"
        self.assertEqual(dict(LecturerResponseDTO.from_lecturer(self.obj).data), self.data)

    @patch.object(Lecturer.objects, "all")
    def test_list_and_get(self, all_records):
        self.assertIs(services.list_lecturers(), all_records.return_value)
        self.assertIs(services.get_lecturer("GV001"), self.obj)
        self.get.assert_called_once_with(pk="GV001")

    def test_create_checks_parent_and_unique_id(self):
        self.assertIs(services.create_lecturer(self.data), self.obj)
        self.parent.assert_called_once_with(pk="F01")
        self.existing.assert_called_once_with(pk="GV001")
        self.create.assert_called_once_with(**self.data)
        self.atomic.assert_called_once_with()

    def test_duplicate_id_rejected_before_write(self):
        self.existing.return_value.exists.return_value = True
        with self.assertRaises(services.BusinessValidationError) as caught:
            services.create_lecturer(self.data)
        self.assertIn("lecturer_id", caught.exception.errors)
        self.create.assert_not_called()

    def test_invalid_department_prevents_create_and_update(self):
        self.parent.return_value.exists.return_value = False
        for operation in [lambda: services.create_lecturer(self.data),
                          lambda: services.update_lecturer("GV001", {"department_id": "missing"})]:
            with self.assertRaises(services.BusinessValidationError) as caught:
                operation()
            self.assertIn("department_id", caught.exception.errors)
        self.create.assert_not_called()
        self.obj.save.assert_not_called()

    def test_create_without_department_or_with_null(self):
        for data in [{"lecturer_id": "GV001"}, {"lecturer_id": "GV001", "department_id": None}]:
            self.create.reset_mock()
            services.create_lecturer(data)
            self.create.assert_called_once_with(**data)
        self.parent.assert_not_called()

    def test_update_preserves_id_and_omitted_fields(self):
        services.update_lecturer("GV001", {"lecturer_id": "GV001"})
        self.assertEqual(self.obj.department_id, "F01")
        self.obj.save.assert_not_called()
        self.create.assert_not_called()

    def test_update_changes_department_without_inserting(self):
        result = services.update_lecturer("GV001", {"department_id": "F02"})
        self.assertIs(result, self.obj)
        self.assertEqual(self.obj.department_id, "F02")
        self.assertEqual(self.obj.lecturer_id, "GV001")
        self.obj.save.assert_called_once_with(update_fields=["department"])
        self.create.assert_not_called()

    def test_null_department_clears_relationship(self):
        services.update_lecturer("GV001", {"department_id": None})
        self.assertIsNone(self.obj.department_id)
        self.parent.assert_not_called()
        self.obj.save.assert_called_once_with(update_fields=["department"])

    def test_primary_key_change_is_rejected(self):
        with self.assertRaises(services.BusinessValidationError) as caught:
            services.update_lecturer("GV001", {"lecturer_id": "GV002"})
        self.assertIn("lecturer_id", caught.exception.errors)
        self.assertEqual(self.obj.lecturer_id, "GV001")
        self.obj.save.assert_not_called()
        self.create.assert_not_called()

    def test_delete(self):
        services.delete_lecturer("GV001")
        self.obj.delete.assert_called_once_with()
        self.atomic.assert_called_once_with()

    def test_missing_records(self):
        self.get.side_effect = Lecturer.DoesNotExist
        for operation in [lambda: services.get_lecturer("missing"),
                          lambda: services.update_lecturer("missing", {}),
                          lambda: services.delete_lecturer("missing")]:
            with self.assertRaises(Lecturer.DoesNotExist):
                operation()
        self.obj.save.assert_not_called()
        self.obj.delete.assert_not_called()

    def test_integrity_failures_are_safe_business_errors(self):
        cases = [(self.create, lambda: services.create_lecturer(self.data), "lecturer_id"),
                 (self.obj.save, lambda: services.update_lecturer("GV001", {"department_id": "F02"}), "department_id"),
                 (self.obj.delete, lambda: services.delete_lecturer("GV001"), "lecturer_id")]
        for target, operation, field in cases:
            with self.subTest(field=field):
                target.side_effect = IntegrityError("private SQL details")
                with self.assertRaises(services.BusinessValidationError) as caught:
                    operation()
                self.assertIn(field, caught.exception.errors)
                self.assertNotIn("private SQL", str(caught.exception))
                target.side_effect = None

    def test_deferred_constraint_failure_at_commit_is_translated(self):
        self.atomic.return_value.__exit__.side_effect = IntegrityError("private schema")
        with self.assertRaises(services.BusinessValidationError) as caught:
            services.create_lecturer(self.data)
        self.assertIn("lecturer_id", caught.exception.errors)
        self.assertNotIn("private schema", str(caught.exception))
