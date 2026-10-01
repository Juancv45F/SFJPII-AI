import unittest

from services.keep_alive_service import _health_url


class KeepAliveServiceTests(unittest.TestCase):
    def test_health_url_removes_trailing_slash(self):
        self.assertEqual(
            _health_url("https://sfjpii-back.onrender.com/"),
            "https://sfjpii-back.onrender.com/health",
        )
if __name__ == "__main__":
    unittest.main()
