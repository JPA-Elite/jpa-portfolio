import unittest
from unittest.mock import patch

from flask import Flask

from app.domains import is_local_host, should_track_visit


class VisitTrackingHostTests(unittest.TestCase):
    def test_local_hosts_are_not_tracked(self):
        local_hosts = [
            "",
            None,
            "localhost",
            "localhost:5000",
            "127.0.0.1",
            "127.0.0.1:5000",
            "0.0.0.0",
            "0.0.0.0:5000",
            "[::1]",
            "[::1]:5000",
            "10.1.2.3",
            "172.16.5.4",
            "192.168.1.20",
            "169.254.10.10",
            "devbox",
            "jpastack.local",
            "professional.jpastack.local",
            "social.jpastack.local",
            "config.jpastack.local",
            "app.localhost",
            "app.test",
            "app.internal",
            "app.lan",
            "app.home.arpa",
        ]

        for host in local_hosts:
            with self.subTest(host=host):
                self.assertTrue(is_local_host(host))
                self.assertFalse(should_track_visit(host))

    def test_deployed_hosts_are_tracked(self):
        public_hosts = [
            "jpastack.com",
            "jpastack.com:443",
            "www.jpastack.com",
            "professional.jpastack.com",
            "social.jpastack.com",
            "config.jpastack.com",
            "jpastack.onrender.com",
            "my-portfolio.fly.dev",
            "8.8.8.8",
            "2606:4700:4700::1111",
        ]

        for host in public_hosts:
            with self.subTest(host=host):
                self.assertFalse(is_local_host(host))
                self.assertTrue(should_track_visit(host))


class VisitTrackingRequestTests(unittest.TestCase):
    def _build_app(self):
        from app import app as app_module

        app = Flask(__name__)
        app.add_url_rule(
            "/",
            endpoint="pages.portfolio",
            view_func=lambda: "ok",
        )
        app.before_request(app_module.record_page_visit)
        return app, app_module

    def test_local_request_does_not_start_visit_recording(self):
        app, app_module = self._build_app()
        client = app.test_client()

        with patch.object(app_module.threading, "Thread") as worker:
            response = client.get("/", base_url="http://localhost:5000")

        self.assertEqual(response.status_code, 200)
        worker.assert_not_called()

    def test_deployed_request_starts_visit_recording(self):
        app, app_module = self._build_app()
        client = app.test_client()

        headers = {
            "User-Agent": "visit-tracking-test-agent",
            "X-Forwarded-For": "203.0.113.10",
        }

        with patch.object(app_module.threading, "Thread") as worker:
            response = client.get(
                "/",
                base_url="https://jpastack.com",
                headers=headers,
            )

        self.assertEqual(response.status_code, 200)
        worker.assert_called_once()
        _args, kwargs = worker.call_args
        self.assertEqual(
            kwargs["args"],
            (
                "/",
                "203.0.113.10",
                "visit-tracking-test-agent",
                app_module.current_site("jpastack.com"),
            ),
        )
        self.assertTrue(kwargs["daemon"])


if __name__ == "__main__":
    unittest.main()
