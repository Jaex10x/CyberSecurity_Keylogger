import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.encryption import EncryptionManager

class TestEncryptionManager(unittest.TestCase):

    def setUp(self):
        self.crypto = EncryptionManager()

    def test_encrypt_decrypt_roundtrip(self):
        original = "Hello, CyberSentinel! Testing encryption."
        encrypted = self.crypto.encrypt(original)
        self.assertNotEqual(encrypted, original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypt_empty_string(self):
        encrypted = self.crypto.encrypt("")
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, "")

    def test_encrypt_unicode(self):
        original = "こんにちは世界 🔐 Ñoño"
        encrypted = self.crypto.encrypt(original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypt_long_text(self):
        original = "A" * 10000
        encrypted = self.crypto.encrypt(original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_different_encryptions_differ(self):
        original = "test data"
        enc1 = self.crypto.encrypt(original)
        enc2 = self.crypto.encrypt(original)
        self.assertNotEqual(enc1, enc2)

    def test_get_status(self):
        status = self.crypto.get_status()
        self.assertIn("enabled", status)
        self.assertIn("key_loaded", status)
        self.assertTrue(status["enabled"])
        self.assertTrue(status["key_loaded"])

    def test_key_derivation(self):
        key1, salt1 = EncryptionManager.derive_key_from_password("password123")
        key2, salt2 = EncryptionManager.derive_key_from_password(
            "password123", salt=salt1
        )
        self.assertEqual(key1, key2)

        key3, _ = EncryptionManager.derive_key_from_password("different", salt=salt1)
        self.assertNotEqual(key1, key3)

class TestSystemProfiler(unittest.TestCase):

    def setUp(self):
        from utils.system_info import SystemProfiler
        self.profiler = SystemProfiler()

    def test_collect_all_returns_dict(self):
        profile = self.profiler.collect_all()
        self.assertIsInstance(profile, dict)

    def test_profile_has_required_keys(self):
        profile = self.profiler.collect_all()
        required_keys = ["os_info", "hardware", "network", "user_info", "processes"]
        for key in required_keys:
            self.assertIn(key, profile)

    def test_os_info_fields(self):
        profile = self.profiler.collect_all()
        os_info = profile["os_info"]
        self.assertIn("system", os_info)
        self.assertIn("python_version", os_info)
        self.assertIn("machine", os_info)

    def test_get_summary_returns_string(self):
        summary = self.profiler.get_summary()
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

class TestConsentManager(unittest.TestCase):

    def setUp(self):
        from utils.consent import ConsentManager
        self.consent = ConsentManager()

    def test_initial_state_no_consent(self):
        self.assertFalse(self.consent.verify_consent())

    def test_consent_history_empty(self):
        history = self.consent.get_consent_history()
        self.assertIsInstance(history, list)

class TestFileHandler(unittest.TestCase):

    def setUp(self):
        from storage.file_handler import FileHandler
        self.handler = FileHandler()

    def test_list_log_files_returns_list(self):
        files = self.handler.list_log_files()
        self.assertIsInstance(files, list)

    def test_storage_stats_returns_dict(self):
        stats = self.handler.get_storage_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_files", stats)
        self.assertIn("total_size_mb", stats)

if __name__ == "__main__":
    unittest.main(verbosity=2)
