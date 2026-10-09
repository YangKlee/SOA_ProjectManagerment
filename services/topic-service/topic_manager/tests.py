from django.test import SimpleTestCase

from .models import Topic


class TopicServiceTests(SimpleTestCase):
    def test_topic_mapping_is_database_first(self):
        self.assertFalse(Topic._meta.managed)
        self.assertEqual(Topic._meta.db_table, "Topics")

    def test_health(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "topic-service")
