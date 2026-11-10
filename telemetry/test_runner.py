"""Always isolate MongoDB integration tests, including database migrations."""
from uuid import uuid4
from django.conf import settings
from django.test import override_settings
from django.test.runner import DiscoverRunner
from .mongo import database


class HybridTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        self.mongo_database_name = 'nodeverse_test_' + uuid4().hex
        self.mongo_override = override_settings(MONGODB_DATABASE=self.mongo_database_name)
        self.mongo_override.enable()
        try:
            return super().setup_databases(**kwargs)
        except Exception:
            self._clean_mongo()
            raise

    def _clean_mongo(self):
        try:
            db = database()
            if db.name == self.mongo_database_name and db.name.startswith('nodeverse_test_'):
                db.client.drop_database(db.name)
        finally:
            self.mongo_override.disable()

    def teardown_databases(self, old_config, **kwargs):
        try:
            super().teardown_databases(old_config, **kwargs)
        finally:
            self._clean_mongo()
