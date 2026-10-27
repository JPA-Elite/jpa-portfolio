import unittest

from flask import Flask

from app.domains import (
    PROFESSIONAL_PERSONAL_PATHS,
    resolve_domain_redirect,
    resolve_professional_redirect,
)


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


class LandingRedirectTests(unittest.TestCase):
    def test_landing_root_redirects_to_professional_host(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_domain_redirect("jpastack.local", "/"),
                "http://professional.jpastack.local/",
            )

    def test_landing_pages_redirect_to_professional_host(self):
        app = _make_app()
        with app.app_context():
            for path in ("/portfolio", "/gallery", "/build"):
                with self.subTest(path=path):
                    self.assertEqual(
                        resolve_domain_redirect("jpastack.local", path),
                        f"http://professional.jpastack.local{path}",
                    )

    def test_landing_redirect_preserves_query_string(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_domain_redirect("jpastack.local", "/gallery", "page=2"),
                "http://professional.jpastack.local/gallery?page=2",
            )

    def test_landing_personal_pages_redirect_to_social_host(self):
        app = _make_app()
        with app.app_context():
            for path in PROFESSIONAL_PERSONAL_PATHS:
                with self.subTest(path=path):
                    self.assertEqual(
                        resolve_domain_redirect("jpastack.local", path),
                        f"http://social.jpastack.local{path}",
                    )

    def test_landing_redirect_preserves_non_standard_port(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_domain_redirect("jpastack.local:4173", "/portfolio"),
                "http://professional.jpastack.local:4173/portfolio",
            )

    def test_landing_admin_pages_redirect_to_admin_host(self):
        app = _make_app()
        with app.app_context():
            self.assertEqual(
                resolve_domain_redirect("jpastack.local", "/admin/login"),
                "http://config.jpastack.local/admin/login",
            )

    def test_landing_shared_paths_are_not_redirected(self):
        app = _make_app()
        with app.app_context():
            for path in ("/sitemap.xml", "/robots.txt", "/api/portfolio"):
                with self.subTest(path=path):
                    self.assertIsNone(resolve_domain_redirect("jpastack.local", path))

    def test_professional_and_social_hosts_are_not_redirected(self):
        app = _make_app()
        with app.app_context():
            for host in ("professional.jpastack.local", "social.jpastack.local"):
                with self.subTest(host=host):
                    self.assertIsNone(resolve_domain_redirect(host, "/portfolio"))

    def test_landing_equal_to_social_host_is_not_redirected(self):
        app = _make_app()
        app.config["SOCIAL_DOMAIN"] = "jpastack.local"
        with app.app_context():
            self.assertIsNone(resolve_domain_redirect("jpastack.local", "/portfolio"))

    def test_routing_disabled_returns_none(self):
        app = _make_app(routing_enabled=False)
        with app.app_context():
            self.assertIsNone(resolve_domain_redirect("jpastack.local", "/portfolio"))


if __name__ == "__main__":
    unittest.main()
