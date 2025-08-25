from flask import Flask, request, jsonify, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# MongoDB connection from env parts
user = urllib.parse.quote_plus(os.getenv("MONGO_USER", ""))
password = urllib.parse.quote_plus(os.getenv("MONGO_PASS", ""))
host = os.getenv("MONGO_HOST", "")
db_name = os.getenv("MONGO_DB", "")
app.config["MONGO_URI"] = (
    f"mongodb+srv://{user}:{password}@{host}/{db_name}"
    f"?retryWrites=true&w=majority&appName={db_name}"
)

mongo = PyMongo(app)
db = mongo.db

# Serve index.html at root
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

# Serve all static HTML/CSS/JS files
@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Save user (document)
@app.route("/add-user", methods=["POST"])
def add_user():
    try:
        data = request.get_json() or {}
        # Optional: quick log of size (base64 photos can be big)
        try:
            approx_kb = len(request.data) // 1024
            app.logger.info(f"/add-user payload ~{approx_kb} KB")
        except Exception:
            pass

        db.users.insert_one(data)
        return jsonify({"message": "✅ Sale deed saved successfully"})
    except Exception as e:
        app.logger.exception("Insert error")
        return jsonify({"message": "❌ Failed to save"}), 500

# Get users
@app.route("/get-users", methods=["GET"])
def get_users():
    try:
        users = list(db.users.find())
        # Return proper JSON content type with bson -> json conversion
        return app.response_class(dumps(users), mimetype="application/json"), 200
    except Exception as e:
        app.logger.exception("Fetch error")
        return jsonify([]), 200

# Delete user
@app.route("/delete-user", methods=["POST"])
def delete_user():
    try:
        data = request.get_json() or {}
        _id = data.get("id")
        if _id is None:
            return jsonify({"message": "❌ Missing id"}), 400
        db.users.delete_one({"id": _id})
        return jsonify({"message": "✅ Record deleted"})
    except Exception as e:
        app.logger.exception("Delete error")
        return jsonify({"message": "❌ Failed to delete"}), 500

if __name__ == "__main__":
    app.run(debug=True)
