from flask import Flask, jsonify

from backend.middleware.network import trusted_network_guard


def _build_app():
    app = Flask(__name__)

    @app.before_request
    def _guard():
        return trusted_network_guard()

    @app.route("/ping")
    def ping():
        return jsonify({"ok": True})

    return app


def test_trusted_network_guard_allows_when_not_enforced(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "0")
    monkeypatch.setenv("ENFORCE_TRUSTED_NETWORK", "0")

    app = _build_app()
    client = app.test_client()

    response = client.get("/ping", environ_overrides={"REMOTE_ADDR": "203.0.113.200"})
    assert response.status_code == 200


def test_trusted_network_guard_blocks_untrusted_when_enforced(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "0")
    monkeypatch.setenv("ENFORCE_TRUSTED_NETWORK", "1")
    monkeypatch.setenv("TRUSTED_IPS", "198.51.100.10")
    monkeypatch.setenv("TRUSTED_CIDRS", "")

    app = _build_app()
    client = app.test_client()

    response = client.get("/ping", environ_overrides={"REMOTE_ADDR": "203.0.113.200"})
    assert response.status_code == 403


def test_trusted_network_guard_allows_trusted_ip_when_enforced(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "0")
    monkeypatch.setenv("ENFORCE_TRUSTED_NETWORK", "1")
    monkeypatch.setenv("TRUSTED_IPS", "198.51.100.10")
    monkeypatch.setenv("TRUSTED_CIDRS", "")

    app = _build_app()
    client = app.test_client()

    response = client.get("/ping", environ_overrides={"REMOTE_ADDR": "198.51.100.10"})
    assert response.status_code == 200


def test_trusted_network_guard_allows_local_in_debug(monkeypatch):
    monkeypatch.setenv("FLASK_DEBUG", "1")
    monkeypatch.setenv("ENFORCE_TRUSTED_NETWORK", "1")

    app = _build_app()
    client = app.test_client()

    response = client.get("/ping", environ_overrides={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200
