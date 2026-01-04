from flask import Flask, request, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from dotenv import load_dotenv
import os
import urllib.parse

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
        offset = int(request.args.get("offset", 62))   # how many to skip
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


if __name__ == "__main__":
    # NEVER RUN DEBUG TRUE IN PRODUCTION
    app.run(host="0.0.0.0", port=10000, debug=False)
