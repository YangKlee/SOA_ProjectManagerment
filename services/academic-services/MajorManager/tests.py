from django.test import SimpleTestCase
from .models import Major
class MajorDatabaseFirstTests(SimpleTestCase):
 def test_mapping(self): self.assertFalse(Major._meta.managed); self.assertEqual(Major._meta.db_table,"Majors")
