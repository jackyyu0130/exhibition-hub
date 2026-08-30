import ssl
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.tls_compat import (  # noqa: E402
    CULTURE_MINISTRY_HTTPS_PREFIX,
    CultureMinistryTLSAdapter,
    create_culture_ministry_session,
    culture_ministry_ssl_context,
)


class CultureMinistryTlsCompatibilityTests(unittest.TestCase):
    def test_context_keeps_ca_and_hostname_verification(self):
        context = culture_ministry_ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_context_disables_only_optional_x509_strict_mode(self):
        strict_flag = getattr(ssl, "VERIFY_X509_STRICT", 0)
        if strict_flag:
            strict_context = ssl.create_default_context()
            strict_context.verify_flags |= strict_flag
            with mock.patch(
                "exhibition_hub.tls_compat.ssl.create_default_context",
                return_value=strict_context,
            ):
                context = culture_ministry_ssl_context()
            self.assertFalse(context.verify_flags & strict_flag)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)

    def test_adapter_is_scoped_to_culture_ministry_origin(self):
        session = create_culture_ministry_session()
        try:
            adapter = session.get_adapter(CULTURE_MINISTRY_HTTPS_PREFIX)
            self.assertIsInstance(adapter, CultureMinistryTLSAdapter)
            self.assertNotIsInstance(
                session.get_adapter("https://example.com/"),
                CultureMinistryTLSAdapter,
            )
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
