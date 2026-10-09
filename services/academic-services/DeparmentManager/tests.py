from django.test import SimpleTestCase
from .models import Department
from .serializers import DepartmentRequestDTO
class DepartmentDatabaseFirstTests(SimpleTestCase):
 def test_mapping_and_dto(self):
  self.assertFalse(Department._meta.managed); self.assertEqual(Department._meta.db_table,"Faculties"); self.assertTrue(DepartmentRequestDTO(data={"department_id":"F01","name":"IT"}).is_valid())
