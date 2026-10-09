from django.test import SimpleTestCase
from .models import SubMajor
class SubMajorDatabaseFirstTests(SimpleTestCase):
 def test_mapping(self): self.assertFalse(SubMajor._meta.managed); self.assertEqual(SubMajor._meta.db_table,"Specializations")
