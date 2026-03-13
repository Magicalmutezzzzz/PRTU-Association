from flask import Flask, request, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from dotenv import load_dotenv
import os
import urllib.parse
import ctypes
import base64
import io
from PIL import Image


load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

user = urllib.parse.quote_plus(os.getenv("MONGO_USER", ""))
password = urllib.parse.quote_plus(os.getenv("MONGO_PASS", ""))
host = os.getenv("MONGO_HOST", "")
db_name = os.getenv("MONGO_DB", "")

app.config["MONGO_URI"] = (
    f"mongodb+srv://{user}:{password}@{host}/{db_name}"
    f"?retryWrites=true&w=majority"
)

mongo = PyMongo(app)
db = mongo.db

# -------------------------------
# SecuGen Scanner Setup
# -------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tell Windows where DLLs are located
os.add_dll_directory(BASE_DIR)

# Load main SecuGen library
sgfplib = ctypes.WinDLL(os.path.join(BASE_DIR, "sgfplib.dll"))

IMAGE_WIDTH = 300
IMAGE_HEIGHT = 400

sensor = ctypes.c_void_p()

SG_DEV_AUTO = 255

r1 = sgfplib.CreateSGFPMObject(ctypes.byref(sensor))
r2 = sgfplib.SGFPM_Init(sensor, SG_DEV_AUTO)
r3 = sgfplib.SGFPM_OpenDevice(sensor, 0)

print("CreateSGFPMObject:", r1)
print("SGFPM_Init:", r2)
print("SGFPM_OpenDevice:", r3)

if r1 != 0 or r2 != 0 or r3 != 0:
    raise Exception("SecuGen initialization failed")

print("SecuGen scanner initialized")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route("/add-user", methods=["POST"])
def add_user():
    try:
        data = request.get_json(force=True) or {}
        db.users.insert_one(data)
        return jsonify({"message": "Saved"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# PAGINATED USERS (SAFE)
@app.route("/get-users", methods=["GET"])
def get_users():
    try:
        offset = int(request.args.get("offset", 145))   # how many to skip
        limit = int(request.args.get("limit", 100))    # how many to return

        cursor = db.users.find().skip(offset).limit(limit)

        return app.response_class(
            dumps(list(cursor)),
            mimetype="application/json"
        )
    except Exception as e:
        return jsonify([]), 200


@app.route("/delete-user", methods=["POST"])
def delete_user():
    try:
        data = request.get_json() or {}
        _id = data.get("id")
        if not _id:
            return jsonify({"message": "Missing id"}), 400

        db.users.delete_one({"id": _id})
        return jsonify({"message": "Deleted"}), 200
    except Exception as e:
        return jsonify({"message": "Failed"}), 500

@app.route("/verify", methods=["GET"])
def verify_api():
    try:
        sr = request.args.get("sr")
        dn = request.args.get("dn")

        if not sr or not dn:
            return jsonify({}), 400

        doc = db.users.find_one({
            "metaNotarySrNo": sr,
            "metaDocumentNumber": dn
        })

        return app.response_class(dumps(doc), mimetype="application/json")
    except:
        return jsonify({}), 500


@app.route("/capture-fingerprint", methods=["POST"])
def capture_fingerprint():
    try:

        img_buffer = (ctypes.c_ubyte * (IMAGE_WIDTH * IMAGE_HEIGHT))()

        result = sgfplib.SGFPM_GetImage(sensor, img_buffer)

        if result != 0:
            return jsonify({
                "success": False,
                "error": f"Capture failed ({result})"
            })

        img = Image.frombytes(
            "L",
            (IMAGE_WIDTH, IMAGE_HEIGHT),
            bytes(img_buffer)
        )

        buf = io.BytesIO()
        img.save(buf, format="BMP")

        encoded = base64.b64encode(buf.getvalue()).decode()

        return jsonify({
            "success": True,
            "image": encoded
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    # NEVER RUN DEBUG TRUE IN PRODUCTION
    app.run(host="0.0.0.0", port=10000, debug=False)
