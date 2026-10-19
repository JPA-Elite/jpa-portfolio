import unittest

from flask import Flask

from app.domains import PROFESSIONAL_PERSONAL_PATHS, resolve_professional_redirect


def _make_app(routing_enabled=True, admin_domain="config.jpastack.local"):
    app = Flask(__name__)
    app.config["LANDING_DOMAIN"] = "jpastack.local"
    app.config["PROFESSIONAL_DOMAIN"] = "professional.jpastack.local"
    app.config["SOCIAL_DOMAIN"] = "social.jpastack.local"
    app.config["ADMIN_DOMAIN"] = admin_domain
    app.config["DOMAIN_ROUTING_ENABLED"] = routing_enabled
    return app


class ProfessionalRedirectTests(unittest.TestCase):
    def test_personal_pages_redirect_to_professional_root(self):
        app = _make_app()
        with app.app_context():
            for path in PROFESSIONAL_PERSONAL_PATHS:
                with self.subTest(path=path):
                    self.assertEqual(
                        resolve_professional_redirect(
                            "professional.jpastack.local", path
                        ),
                        "http://professional.jpastack.local/",
                    )

    def test_personal_pages_redirect_with_trailing_slash(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/vlog/"
                ),
                "http://professional.jpastack.local/",
            )

    def test_admin_pages_redirect_to_professional_root(self):
        app = _make_app()
        with app.app_context():
            for path in ("/admin", "/admin/login", "/admin/dashboard"):
                with self.subTest(path=path):
                    self.assertEqual(
                        resolve_professional_redirect(
                            "professional.jpastack.local", path
                        ),
                        "http://professional.jpastack.local/",
                    )

    def test_redirect_uses_request_scheme(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/music", "https"
                ),
                "https://professional.jpastack.local/",
            )

    def test_redirect_preserves_non_standard_port(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_professional_redirect(
                    "professional.jpastack.local:5000", "/donation"
                ),
                "http://professional.jpastack.local:5000/",
            )

    def test_public_professional_pages_are_not_redirected(self):
        app = _make_app()
        with app.app_context():
            for path in ("/", "/portfolio", "/gallery", "/build"):
                with self.subTest(path=path):
                    self.assertIsNone(
                        resolve_professional_redirect(
                            "professional.jpastack.local", path
                        )
                    )

    def test_other_hosts_are_not_redirected(self):
        app = _make_app()
        with app.app_context():
            for host in ("jpastack.local", "social.jpastack.local", "config.jpastack.local"):
                with self.subTest(host=host):
                    self.assertIsNone(
                        resolve_professional_redirect(host, "/vlog")
                    )

    def test_non_get_requests_are_not_redirected(self):
        app = _make_app()
        with app.app_context():
            self.assertIsNone(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/admin/login", "http", "POST"
                )
            )

    def test_routing_disabled_returns_none(self):
        app = _make_app(routing_enabled=False)
        with app.app_context():
            self.assertIsNone(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/vlog"
                )
            )

    def test_admin_paths_stay_available_without_admin_domain(self):
        app = _make_app(admin_domain="")
        with app.app_context():
            self.assertIsNone(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/admin/login"
                )
            )
            self.assertEqual(
                resolve_professional_redirect(
                    "professional.jpastack.local", "/vlog"
                ),
                "http://professional.jpastack.local/",
            )


if __name__ == "__main__":
    unittest.main()
