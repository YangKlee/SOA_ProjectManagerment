from django.test import SimpleTestCase
from .models import Student
class StudentDatabaseFirstTests(SimpleTestCase):
 def test_mapping(self): self.assertFalse(Student._meta.managed); self.assertEqual(Student._meta.db_table,"Students")
