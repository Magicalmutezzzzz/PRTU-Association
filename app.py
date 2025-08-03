from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.json_util import dumps
from dotenv import load_dotenv
import os
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Build MONGO_URI from components
user = urllib.parse.quote_plus(os.getenv("MONGO_USER"))
password = urllib.parse.quote_plus(os.getenv("MONGO_PASS"))
host = os.getenv("MONGO_HOST")
db_name = os.getenv("MONGO_DB")
app.config["MONGO_URI"] = f"mongodb+srv://{user}:{password}@{host}/{db_name}?retryWrites=true&w=majority&appName={db_name}"

# Setup Mongo
mongo = PyMongo(app)
db = mongo.db

# Routes
@app.route('/add-user', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        db.users.insert_one(data)
        return jsonify({"message": "✅ Sale deed saved successfully"})
    except Exception as e:
        print("Error inserting:", e)
        return jsonify({"message": "❌ Failed to save"}), 500

@app.route('/get-users', methods=['GET'])
def get_users():
    try:
        users = list(db.users.find())
        return dumps(users), 200
    except Exception as e:
        print("Error fetching users:", e)
        return jsonify([])

@app.route('/delete-user', methods=['POST'])
def delete_user():
    try:
        data = request.get_json()
        db.users.delete_one({'id': data['id']})
        return jsonify({"message": "✅ Record deleted"})
    except Exception as e:
        print("Error deleting user:", e)
        return jsonify({"message": "❌ Failed to delete"}), 500

if __name__ == '__main__':
    app.run(debug=True)
