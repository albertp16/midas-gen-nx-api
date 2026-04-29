"""
Flask backend for MIDAS Gen NX API Dashboard.
Serves the frontend and provides a CORS proxy to the MIDAS API.
"""
import os
import mimetypes
import tempfile
import requests
from flask import Flask, send_from_directory, request, jsonify, Response, send_file

app = Flask(__name__, static_folder=".", static_url_path="")

MIDAS_BASE_URL = os.environ.get("MIDAS_BASE_URL", "https://moa-engineers.midasit.com:443/gen")

# Folder used for /view/capture screenshots produced by MIDAS. Both MIDAS Gen
# and this Flask server must be running on the same machine since /view/capture
# writes to local disk on whatever host is running MIDAS.
CAPTURE_DIR = os.path.join(tempfile.gettempdir(), "midas_capture")
os.makedirs(CAPTURE_DIR, exist_ok=True)


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


@app.route("/api/capture-dir")
def capture_dir():
    """Returns the absolute path the frontend should pass as EXPORT_PATH for
    /view/capture. A single shared folder makes cleanup and path validation
    trivial on the /api/local-image side."""
    return jsonify({"dir": CAPTURE_DIR})


@app.route("/api/local-image")
def local_image():
    """Serve a JPG that MIDAS just wrote to CAPTURE_DIR. Restricted to that
    folder so the endpoint can't be used to read arbitrary files."""
    name = request.args.get("name", "")
    if not name or "/" in name or "\\" in name or ".." in name:
        return jsonify({"error": "Invalid name"}), 400

    full = os.path.realpath(os.path.join(CAPTURE_DIR, name))
    if not full.startswith(os.path.realpath(CAPTURE_DIR) + os.sep):
        return jsonify({"error": "Path escapes capture dir"}), 400
    if not os.path.isfile(full):
        return jsonify({"error": "File not found"}), 404

    mime = mimetypes.guess_type(full)[0] or "image/jpeg"
    resp = send_file(full, mimetype=mime)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
