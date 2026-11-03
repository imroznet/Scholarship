import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def _setup(self, env):
        command = [sys.executable, "-c", "import django; django.setup()"]
        return subprocess.run(
            command,
            cwd="/workspace",
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _env(self, **extra):
        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
        env["SECRET_KEY"] = "p" * 48
        env["ALLOWED_HOSTS"] = "scholarship.example.com"
        env["DEBUG"] = "False"
        env["DATABASE_URL"] = "postgres://scholarship:example@127.0.0.1:5432/scholarship"
        env.pop("DJANGO_SECRET_KEY", None)
        env.update(extra)
        return env

    def test_sqlite_is_rejected(self):
        result = self._setup(self._env(DATABASE_URL="sqlite:///db.sqlite3"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SQLite", result.stderr)

    def test_debug_and_short_secret_are_rejected(self):
        debug = self._setup(self._env(DEBUG="True"))
        self.assertNotEqual(debug.returncode, 0)
        self.assertIn("DEBUG", debug.stderr)
        short = self._setup(self._env(SECRET_KEY="short-secret"))
        self.assertNotEqual(short.returncode, 0)
        self.assertIn("SECRET_KEY", short.stderr)

    def test_postgres_configuration_imports(self):
        result = self._setup(self._env())
        self.assertEqual(result.returncode, 0, result.stderr)
