"""
Flask backend for MIDAS Gen NX API Dashboard.
Serves the frontend and provides a CORS proxy to the MIDAS API.
"""
import os
import requests
from flask import Flask, send_from_directory, request, jsonify, Response

app = Flask(__name__, static_folder=".", static_url_path="")

MIDAS_BASE_URL = os.environ.get("MIDAS_BASE_URL", "https://moa-engineers.midasit.com:443/gen")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/proxy", methods=["GET", "POST", "PUT", "DELETE"])
def proxy():
    """
    CORS proxy to forward requests to the MIDAS Gen API.
    Frontend sends: /api/proxy?endpoint=/db/node
    Headers are forwarded including MAPI-Key.
    """
    endpoint = request.args.get("endpoint", "")
    if not endpoint:
        return jsonify({"error": "Missing endpoint parameter"}), 400

    url = MIDAS_BASE_URL + endpoint
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": request.headers.get("MAPI-Key", ""),
    }

    try:
        if request.method == "GET":
            resp = requests.get(url, headers=headers, timeout=60)
        elif request.method == "POST":
            resp = requests.post(url, headers=headers, json=request.get_json(silent=True), timeout=120)
        elif request.method == "PUT":
            resp = requests.put(url, headers=headers, json=request.get_json(silent=True), timeout=60)
        elif request.method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=60)
        else:
            return jsonify({"error": "Unsupported method"}), 405

        response = Response(resp.content, status=resp.status_code)
        response.headers["Content-Type"] = resp.headers.get("Content-Type", "application/json")
        return response

    except requests.exceptions.Timeout:
        return jsonify({"error": "MIDAS API request timed out"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach MIDAS API"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
