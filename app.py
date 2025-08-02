# app.py
# NOTE: This app.py uses separate env vars for credentials and safely encodes them.
# Remove or ignore any old server.js and old app.py versions.

"""
Flask backend for PRTU dashboard: serves static files from /public,
provides CRUD endpoints to MongoDB Atlas using pymongo,
with credentials URL-encoded per RFC 3986.
"""
import os
import base64
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_pymongo import PyMongo
from bson.binary import Binary
from dotenv import load_dotenv
from urllib.parse import quote_plus

# ---------------------
# 1. Load environment
# ---------------------
load_dotenv()  # reads .env in project root
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')  # e.g. cluster0.abcd1.mongodb.net
MONGO_DB   = os.getenv('MONGO_DB', 'prtuDB')

# Validate credentials
if not all([MONGO_USER, MONGO_PASS, MONGO_HOST]):
    raise RuntimeError("❌ Please set MONGO_USER, MONGO_PASS, and MONGO_HOST in your environment.")

# Quote username & password for special chars
user_quoted = quote_plus(MONGO_USER)
pass_quoted = quote_plus(MONGO_PASS)

# Build the URI string
MONGO_URI = (
    f"mongodb+srv://{user_quoted}:{pass_quoted}@{MONGO_HOST}/{MONGO_DB}"
    "?retryWrites=true&w=majority"
)

# ---------------------
# 2. App init & config
# ---------------------
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)

# Shortcut to users collection
users_col = mongo.db.get_collection('users')

# ---------------------
# 3. Helper: parse base64 image data
# ---------------------
def parse_base64_image(data_url):
    if not data_url:
        return None
    try:
        header, b64data = data_url.split(',', 1)
        mime = header.split(';')[0].split(':')[1]
        return {'data': Binary(base64.b64decode(b64data)), 'contentType': mime}
    except Exception:
        return None

# ---------------------
# 4. Serve static files
# ---------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # Serve index.html if path missing or not found
    if path == '' or not os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', 'index.html')
    return send_from_directory('public', path)

# ---------------------
# 5. API routes
# ---------------------
@app.route('/get-users', methods=['GET'])
def get_users():
    docs = []
    for u in users_col.find():
        item = {k: u.get(k) for k in [
            'id','name','age','occupation','address','contact','idNumber',
            'documentNumber','notarySrNo','documentType','executingParties',
            'propertyAddress','propertyValue'
        ]}
        if u.get('photo'):
            item['photoData'] = f"data:{u['photo']['contentType']};base64," + base64.b64encode(u['photo']['data']).decode()
        if u.get('thumbImg'):
            item['thumbData'] = f"data:{u['thumbImg']['contentType']};base64," + base64.b64encode(u['thumbImg']['data']).decode()
        docs.append(item)
    return jsonify(docs)

@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json(force=True)
    photo = parse_base64_image(data.get('photoData',''))
    thumb = parse_base64_image(data.get('thumbData',''))
    doc = {
        **{k: data.get(k) for k in [
            'id','name','age','occupation','address','contact','idNumber',
            'documentNumber','notarySrNo','documentType','executingParties',
            'propertyAddress','propertyValue'
        ]},
        'photo': photo,
        'thumbImg': thumb
    }
    users_col.insert_one(doc)
    return jsonify({'message':'✅ User added successfully'})

@app.route('/update-user', methods=['POST'])
def update_user():
    data = request.get_json(force=True)
    photo = parse_base64_image(data.get('photoData',''))
    thumb = parse_base64_image(data.get('thumbData',''))
    update_fields = {k: data[k] for k in [
        'name','age','occupation','address','contact','idNumber',
        'documentNumber','notarySrNo','documentType','executingParties',
        'propertyAddress','propertyValue'
    ] if data.get(k) is not None}
    if photo: update_fields['photo'] = photo
    if thumb: update_fields['thumbImg'] = thumb
    result = users_col.update_one({'id':data.get('id')},{'$set':update_fields})
    if result.matched_count:
        return jsonify({'message':'✏️ User updated successfully'})
    abort(404,description='❌ User not found')

@app.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json(force=True)
    result = users_col.delete_one({'id':data.get('id')})
    if result.deleted_count:
        return jsonify({'message':'🗑️ User deleted successfully'})
    abort(404,description='❌ User not found')

# ---------------------
# 6. Run server
# ---------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT',3000))
    app.run(host='0.0.0.0',port=port)

# ---------------------
# Notes for Render setup
# ---------------------
# In Render Dashboard -> Environment:
#   - MONGO_USER: your Atlas username
#   - MONGO_PASS: your Atlas password (will be quoted)
#   - MONGO_HOST: e.g. cluster0.abcd1.mongodb.net
#   - MONGO_DB: your database name (default prtuDB)
