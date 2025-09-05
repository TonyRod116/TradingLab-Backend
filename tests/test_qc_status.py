"""
Tests for QuantConnect status handling
"""
import unittest
from utils.json_ci import get_ci
from strategies.domain import normalize_status, QCStatus


class TestJsonCI(unittest.TestCase):
    """Test case-insensitive JSON field access"""
    
    def test_get_ci_case_insensitive(self):
        """Test case-insensitive field access"""
        d = {"Status": "Running", "Progress": 12.3}
        self.assertEqual(get_ci(d, "status"), "Running")
        self.assertEqual(get_ci(d, "PROGRESS"), 12.3)
        self.assertEqual(get_ci(d, "missing", default=0), 0)
    
    def test_get_ci_multiple_keys(self):
        """Test multiple key fallback"""
        d = {"state": "Completed", "Status": "Running"}
        # Should return first match
        self.assertEqual(get_ci(d, "Status", "state"), "Running")
        # Should return second match if first not found
        d2 = {"state": "Completed"}
        self.assertEqual(get_ci(d2, "Status", "state"), "Completed")
    
    def test_get_ci_invalid_input(self):
        """Test with invalid input"""
        self.assertIsNone(get_ci(None, "key"))
        self.assertEqual(get_ci("string", "key", default="default"), "default")


class TestStatusNormalization(unittest.TestCase):
    """Test status normalization"""
    
    def test_normalize_status_variations(self):
        """Test status normalization with various inputs"""
        test_cases = [
            ("Queued", "Queued"),
            ("queued", "Queued"),
            ("QUEUED", "Queued"),
            ("Running", "Running"),
            ("running", "Running"),
            ("Completed", "Completed"),
            ("completed", "Completed"),
            ("complete", "Completed"),
            ("Error", "Failed"),
            ("error", "Failed"),
            ("Failed", "Failed"),
            ("failed", "Failed"),
            ("Aborted", "Aborted"),
            ("aborted", "Aborted"),
            ("abort", "Aborted"),
            (None, "Unknown"),
            ("", "Unknown"),
            ("weird", "Unknown"),
            (123, "Unknown"),
        ]
        
        for raw, expect in test_cases:
            with self.subTest(raw=raw):
                result = normalize_status(raw)
                self.assertEqual(result.value, expect)
                self.assertIsInstance(result, QCStatus)
    
    def test_normalize_status_whitespace(self):
        """Test status normalization with whitespace"""
        self.assertEqual(normalize_status("  Running  ").value, "Running")
        self.assertEqual(normalize_status("\tQueued\n").value, "Queued")


class TestQCStatusEnum(unittest.TestCase):
    """Test QCStatus enum"""
    
    def test_enum_values(self):
        """Test enum values are correct"""
        self.assertEqual(QCStatus.QUEUED.value, "Queued")
        self.assertEqual(QCStatus.RUNNING.value, "Running")
        self.assertEqual(QCStatus.COMPLETED.value, "Completed")
        self.assertEqual(QCStatus.FAILED.value, "Failed")
        self.assertEqual(QCStatus.ABORTED.value, "Aborted")
        self.assertEqual(QCStatus.UNKNOWN.value, "Unknown")
    
    def test_enum_string_behavior(self):
        """Test enum behaves like string"""
        status = QCStatus.RUNNING
        self.assertEqual(status.value, "Running")
        self.assertEqual(status, "Running")
        self.assertNotEqual(status, "Queued")


if __name__ == '__main__':
    unittest.main()
