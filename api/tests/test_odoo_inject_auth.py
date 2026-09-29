import unittest

from app.services.odoo_inject import auth_failure_message


class OdooAuthMessageTest(unittest.TestCase):
    def test_same_user_and_secret_explains_the_rejection(self):
        text = auth_failure_message("admin", "admin")
        self.assertIn("igual al usuario", text)

    def test_other_secret_asks_to_reconnect(self):
        text = auth_failure_message("admin", "other-secret")
        self.assertNotIn("igual al usuario", text)
        self.assertIn("Vuelva a conectar", text)


if __name__ == "__main__":
    unittest.main()
