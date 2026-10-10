from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from . import services
from .models import Department
from .serializers import DepartmentRequestDTO


class DepartmentServiceTests(SimpleTestCase):
    def test_mapping_and_dto(self):
        self.assertFalse(Department._meta.managed)
        self.assertEqual(Department._meta.db_table, "Faculties")
        self.assertTrue(DepartmentRequestDTO(data={"department_id": "F01", "name": "IT"}).is_valid())

    def test_list_get_and_create(self):
        with patch.object(Department.objects, "all") as operation:
            self.assertIs(services.list_departments(), operation.return_value)
        with patch.object(Department.objects, "get") as operation:
            self.assertIs(services.get_department("F01"), operation.return_value)
            operation.assert_called_once_with(pk="F01")
        with patch.object(Department.objects, "create") as operation:
            data = {"department_id": "F01", "name": "IT"}
            self.assertIs(services.create_department(data), operation.return_value)
            operation.assert_called_once_with(**data)

    @patch.object(Department.objects, "get")
    def test_update_preserves_unsupplied_fields(self, operation):
        department = Department(department_id="F01", name="Old")
        department.save = Mock()
        operation.return_value = department
        self.assertIs(services.update_department("F01", {"name": "New"}), department)
        self.assertEqual(department.department_id, "F01")
        self.assertEqual(department.name, "New")
        department.save.assert_called_once_with()
        operation.assert_called_once_with(pk="F01")

    @patch.object(Department.objects, "get")
    def test_delete(self, operation):
        services.delete_department("F01")
        operation.assert_called_once_with(pk="F01")
        operation.return_value.delete.assert_called_once_with()

    @patch.object(Department.objects, "get", side_effect=Department.DoesNotExist)
    def test_missing_record_operations_raise(self, operation):
        for name, args in [("get_department", ("missing",)),
                           ("update_department", ("missing", {"name": "New"})),
                           ("delete_department", ("missing",))]:
            with self.subTest(name=name), self.assertRaises(Department.DoesNotExist):
                getattr(services, name)(*args)


class DepartmentEndpointTests(SimpleTestCase):
    collection = "/api/departments/"
    detail = "/api/departments/1/"

    def setUp(self):
        self.client = APIClient()
        self.authenticate(1)
        self.data = {"department_id": "1", "name": "IT"}
        self.department = SimpleNamespace(**self.data)

    def authenticate(self, role):
        token = AccessToken()
        token["user_id"] = "test-user"
        token["role"] = role
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def request(self, method, path, data=None):
        return getattr(self.client, method)(path, data=data, format="json")

    def test_crud_delegation_and_responses(self):
        cases = [
            ("get", self.collection, None, "list_departments", (), [self.department], 200, [self.data]),
            ("post", self.collection, self.data, "create_department", (self.data,), self.department, 201, self.data),
            ("get", self.detail, None, "get_department", (1,), self.department, 200, self.data),
            ("put", self.detail, self.data, "update_department", (1, self.data), self.department, 200, self.data),
            ("patch", self.detail, {"name": "IT"}, "update_department", (1, {"name": "IT"}), self.department, 200, self.data),
            ("delete", self.detail, None, "delete_department", (1,), None, 204, None),
        ]
        for method, path, payload, name, args, result, status, expected in cases:
            with self.subTest(method=method, path=path), patch.object(services, name, return_value=result) as operation:
                response = self.request(method, path, payload)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.data, expected)
                operation.assert_called_once_with(*args)
                if status == 204:
                    self.assertEqual(response.content, b"")

    def test_invalid_payload_does_not_call_service(self):
        cases = [("post", self.collection, "create_department", {}),
                 ("put", self.detail, "update_department", {"name": "IT"}),
                 ("patch", self.detail, "update_department", {"name": ""})]
        for method, path, name, payload in cases:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, payload).status_code, 400)
                operation.assert_not_called()

    def test_missing_records_return_404(self):
        cases = [("get", "get_department", None),
                 ("put", "update_department", self.data),
                 ("patch", "update_department", {"name": "IT"}),
                 ("delete", "delete_department", None)]
        for method, name, payload in cases:
            with self.subTest(method=method), patch.object(services, name, side_effect=Department.DoesNotExist):
                self.assertEqual(self.request(method, self.detail, payload).status_code, 404)

    def test_unauthenticated_requests_are_rejected(self):
        self.client.credentials()
        for method, path in [("get", self.collection), ("post", self.collection),
                             ("get", self.detail), ("put", self.detail),
                             ("patch", self.detail), ("delete", self.detail)]:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.request(method, path, self.data).status_code, 401)

    def test_invalid_and_expired_tokens_are_rejected(self):
        token = AccessToken()
        token["user_id"] = "test-user"
        token.set_exp(lifetime=timedelta(seconds=-10))
        for value in ["invalid-token", str(token)]:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {value}")
            self.assertEqual(self.client.get(self.collection).status_code, 401)

    def test_non_admin_cannot_write_or_call_services(self):
        self.authenticate(2)
        cases = [("post", self.collection, "create_department"),
                 ("put", self.detail, "update_department"),
                 ("patch", self.detail, "update_department"),
                 ("delete", self.detail, "delete_department")]
        for method, path, name in cases:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, self.data).status_code, 403)
                operation.assert_not_called()

    def test_non_admin_can_read(self):
        self.authenticate(2)
        with patch.object(services, "list_departments", return_value=[self.department]):
            self.assertEqual(self.client.get(self.collection).status_code, 200)
        with patch.object(services, "get_department", return_value=self.department):
            self.assertEqual(self.client.get(self.detail).status_code, 200)

    @patch.object(services, "create_department")
    def test_detail_post_is_not_allowed(self, operation):
        self.assertEqual(self.request("post", self.detail, self.data).status_code, 405)
        operation.assert_not_called()
