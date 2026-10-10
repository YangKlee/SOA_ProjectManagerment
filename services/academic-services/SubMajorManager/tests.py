from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from . import services
from .models import SubMajor
from .serializers import SubMajorRequestDTO


class SubMajorServiceTests(SimpleTestCase):
    data = {'sub_major_id': '1', 'name': 'IT', 'major_id': '2'}

    def test_mapping_and_dto(self):
        self.assertFalse(SubMajor._meta.managed)
        self.assertEqual(SubMajor._meta.db_table, 'Specializations')
        self.assertTrue(SubMajorRequestDTO(data=self.data).is_valid())

    def test_list_and_get(self):
        with patch.object(SubMajor.objects, "all") as operation:
            self.assertIs(services.list_sub_majors(), operation.return_value)
        with patch.object(SubMajor.objects, "get") as operation:
            self.assertIs(services.get_sub_major("1"), operation.return_value)
            operation.assert_called_once_with(pk="1")

    def test_create_with_valid_relationship(self):
        with patch.object(services.Major.objects, "filter") as parent, \
             patch.object(SubMajor.objects, "create") as create:
            parent.return_value.exists.return_value = True
            self.assertIs(services.create_sub_major(self.data), create.return_value)
            parent.assert_called_once_with(pk="2")
            create.assert_called_once_with(**self.data)

    def test_invalid_parent_prevents_create_and_update(self):
        obj = SubMajor(**self.data)
        obj.save = Mock()
        with patch.object(services.Major.objects, "filter") as parent, \
             patch.object(SubMajor.objects, "create") as create, \
             patch.object(SubMajor.objects, "get", return_value=obj):
            parent.return_value.exists.return_value = False
            for operation in [lambda: services.create_sub_major(self.data),
                              lambda: services.update_sub_major("1", {'major_id': "missing"})]:
                with self.assertRaises(services.BusinessValidationError) as caught:
                    operation()
                self.assertIn('major_id', caught.exception.errors)
            create.assert_not_called()
            obj.save.assert_not_called()

    def test_partial_update_preserves_unsupplied_fields(self):
        obj = SubMajor(**self.data)
        obj.save = Mock()
        with patch.object(SubMajor.objects, "get", return_value=obj), \
             patch.object(services, "_validate") as validate:
            self.assertIs(services.update_sub_major("1", {'name': 'New'}), obj)
            self.assertEqual(getattr(obj, 'sub_major_id'), "1")
            self.assertEqual(getattr(obj, 'name'), 'New')
            obj.save.assert_called_once_with()
            self.assertEqual(validate.call_count, 1)

    def test_delete_and_missing_records(self):
        with patch.object(SubMajor.objects, "get") as get:
            services.delete_sub_major("1")
            get.assert_called_once_with(pk="1")
            get.return_value.delete.assert_called_once_with()
        with patch.object(SubMajor.objects, "get", side_effect=SubMajor.DoesNotExist):
            for operation in [lambda: services.get_sub_major("missing"),
                              lambda: services.update_sub_major("missing", {}),
                              lambda: services.delete_sub_major("missing")]:
                with self.assertRaises(SubMajor.DoesNotExist):
                    operation()


class SubMajorEndpointTests(SimpleTestCase):
    collection = "/api/sub-majors/"
    detail = "/api/sub-majors/1/"
    data = {'sub_major_id': '1', 'name': 'IT', 'major_id': '2'}

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
            ("get", self.collection, None, "list_sub_majors", (), [self.obj], 200, [self.data]),
            ("post", self.collection, self.data, "create_sub_major", (self.data,), self.obj, 201, self.data),
            ("get", self.detail, None, "get_sub_major", (1,), self.obj, 200, self.data),
            ("put", self.detail, self.data, "update_sub_major", (1, self.data), self.obj, 200, self.data),
            ("patch", self.detail, {'name': 'New'}, "update_sub_major", (1, {'name': 'New'}), self.obj, 200, self.data),
            ("delete", self.detail, None, "delete_sub_major", (1,), None, 204, None),
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
            ("post", self.collection, "create_sub_major", {}),
            ("put", self.detail, "update_sub_major", {}),
            ("patch", self.detail, "update_sub_major", {'sub_major_id': ""}),
        ]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, data).status_code, 400)
                operation.assert_not_called()

    def test_business_validation_returns_field_errors(self):
        for method, path, name in [("post", self.collection, "create_sub_major"),
                                   ("put", self.detail, "update_sub_major"),
                                   ("patch", self.detail, "update_sub_major")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=services.BusinessValidationError({'major_id': "Invalid relation."})):
                response = self.request(method, path, self.data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(str(response.data['major_id']), "Invalid relation.")

    def test_missing_records_return_404(self):
        for method, name in [("get", "get_sub_major"), ("put", "update_sub_major"),
                             ("patch", "update_sub_major"), ("delete", "delete_sub_major")]:
            with self.subTest(method=method), patch.object(services, name, side_effect=SubMajor.DoesNotExist):
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
        for method, path, name in [("post", self.collection, "create_sub_major"),
                                   ("put", self.detail, "update_sub_major"),
                                   ("patch", self.detail, "update_sub_major"),
                                   ("delete", self.detail, "delete_sub_major")]:
            with self.subTest(method=method), patch.object(services, name) as operation:
                self.assertEqual(self.request(method, path, self.data).status_code, 403)
                operation.assert_not_called()

    def test_non_admin_reads(self):
        self.authenticate(2)
        with patch.object(services, "list_sub_majors", return_value=[self.obj]):
            self.assertEqual(self.client.get(self.collection).status_code, 200)
        with patch.object(services, "get_sub_major", return_value=self.obj):
            self.assertEqual(self.client.get(self.detail).status_code, 200)

    @patch.object(services, "create_sub_major")
    def test_detail_post_returns_405(self, operation):
        self.assertEqual(self.request("post", self.detail, self.data).status_code, 405)
        operation.assert_not_called()


class SubMajorOptionalParentTests(SimpleTestCase):
    def test_omitted_and_null_parent_skip_relationship_lookup(self):
        for data in [{}, {'major_id': None}]:
            with self.subTest(data=data), patch.object(services.Major.objects, "filter") as parent, \
                 patch.object(SubMajor.objects, "create") as create:
                services.create_sub_major(data)
                parent.assert_not_called()
                create.assert_called_once_with(**data)

    def test_null_parent_clears_existing_relationship(self):
        obj = SubMajor(major_id="2")
        obj.save = Mock()
        with patch.object(SubMajor.objects, "get", return_value=obj), \
             patch.object(services.Major.objects, "filter") as parent:
            services.update_sub_major("1", {'major_id': None})
            self.assertIsNone(obj.major_id)
            parent.assert_not_called()
            obj.save.assert_called_once_with()
