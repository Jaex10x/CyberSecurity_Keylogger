"""
CyberSentinel - Core Module Tests
====================================
Unit tests for the core monitoring modules.
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test encryption module
from utils.encryption import EncryptionManager


class TestEncryptionManager(unittest.TestCase):
    """Tests for the EncryptionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.crypto = EncryptionManager()

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypting then decrypting returns original text."""
        original = "Hello, CyberSentinel! Testing encryption."
        encrypted = self.crypto.encrypt(original)
        self.assertNotEqual(encrypted, original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        encrypted = self.crypto.encrypt("")
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, "")

    def test_encrypt_unicode(self):
        """Test encryption of unicode characters."""
        original = "こんにちは世界 🔐 Ñoño"
        encrypted = self.crypto.encrypt(original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypt_long_text(self):
        """Test encryption of long text."""
        original = "A" * 10000
        encrypted = self.crypto.encrypt(original)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_different_encryptions_differ(self):
        """Test that same text produces different ciphertext each time."""
        original = "test data"
        enc1 = self.crypto.encrypt(original)
        enc2 = self.crypto.encrypt(original)
        # Fernet includes timestamp, so same plaintext -> different ciphertext
        self.assertNotEqual(enc1, enc2)

    def test_get_status(self):
        """Test encryption status reporting."""
        status = self.crypto.get_status()
        self.assertIn("enabled", status)
        self.assertIn("key_loaded", status)
        self.assertTrue(status["enabled"])
        self.assertTrue(status["key_loaded"])

    def test_key_derivation(self):
        """Test password-based key derivation."""
        key1, salt1 = EncryptionManager.derive_key_from_password("password123")
        key2, salt2 = EncryptionManager.derive_key_from_password(
            "password123", salt=salt1
        )
        self.assertEqual(key1, key2)

        # Different password should produce different key
        key3, _ = EncryptionManager.derive_key_from_password("different", salt=salt1)
        self.assertNotEqual(key1, key3)


class TestSystemProfiler(unittest.TestCase):
    """Tests for the SystemProfiler class."""

    def setUp(self):
        from utils.system_info import SystemProfiler
        self.profiler = SystemProfiler()

    def test_collect_all_returns_dict(self):
        """Test that collect_all returns a dictionary."""
        profile = self.profiler.collect_all()
        self.assertIsInstance(profile, dict)

    def test_profile_has_required_keys(self):
        """Test that profile contains all required sections."""
        profile = self.profiler.collect_all()
        required_keys = ["os_info", "hardware", "network", "user_info", "processes"]
        for key in required_keys:
            self.assertIn(key, profile)

    def test_os_info_fields(self):
        """Test OS info contains expected fields."""
        profile = self.profiler.collect_all()
        os_info = profile["os_info"]
        self.assertIn("system", os_info)
        self.assertIn("python_version", os_info)
        self.assertIn("machine", os_info)

    def test_get_summary_returns_string(self):
        """Test that get_summary returns a formatted string."""
        summary = self.profiler.get_summary()
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)


class TestConsentManager(unittest.TestCase):
    """Tests for the ConsentManager class."""

    def setUp(self):
        from utils.consent import ConsentManager
        self.consent = ConsentManager()

    def test_initial_state_no_consent(self):
        """Test that consent is not granted by default."""
        self.assertFalse(self.consent.verify_consent())

    def test_consent_history_empty(self):
        """Test consent history is initially available."""
        history = self.consent.get_consent_history()
        self.assertIsInstance(history, list)


class TestFileHandler(unittest.TestCase):
    """Tests for the FileHandler class."""

    def setUp(self):
        from storage.file_handler import FileHandler
        self.handler = FileHandler()

    def test_list_log_files_returns_list(self):
        """Test that listing log files returns a list."""
        files = self.handler.list_log_files()
        self.assertIsInstance(files, list)

    def test_storage_stats_returns_dict(self):
        """Test storage statistics."""
        stats = self.handler.get_storage_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_files", stats)
        self.assertIn("total_size_mb", stats)


if __name__ == "__main__":
    unittest.main(verbosity=2)
