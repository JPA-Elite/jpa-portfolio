from flask import Flask, jsonify

from backend.middleware.security import require_safe_input, validate_object_id_param


def _create_app():
    app = Flask(__name__)

    @app.route("/safe", methods=["POST"])
    @require_safe_input
    def safe_route():
        return jsonify({"status": "ok"})

    @app.route("/by-id/<item_id>", methods=["GET"])
    @validate_object_id_param("item_id")
    def by_id(item_id):
        return jsonify({"item_id": item_id})

    return app


def test_require_safe_input_blocks_nosql_operator_keys():
    app = _create_app()
    client = app.test_client()

    response = client.post("/safe", json={"$where": "this.password"})

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


def test_require_safe_input_allows_regular_json_payloads():
    app = _create_app()
    client = app.test_client()

    response = client.post("/safe", json={"title": "Hello", "tags": ["a", "b"]})

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_validate_object_id_param_rejects_invalid_id():
    app = _create_app()
    client = app.test_client()

    response = client.get("/by-id/not-an-objectid")

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
