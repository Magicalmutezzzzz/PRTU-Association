# app.py
# NOTE: Remove or ignore the existing server.js file in your repo.
# This app.py file replaces server.js. Commit it as app.py at project root.

"""
Flask backend for PRTU dashboard: serves static files from /public,
provides CRUD endpoints to MongoDB Atlas using pymongo.
"""
import os
import base64
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_pymongo import PyMongo
from bson.binary import Binary
from dotenv import load_dotenv

# ---------------------
# 1. Load environment
# ---------------------
load_dotenv()  # reads .env in project root
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI not set. Define it in a .env file or Render env vars.")

# ---------------------
# 2. App init & config
# ---------------------
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)

# Shortcut to users collection
users_col = mongo.db.get_collection('users')

# ---------------------
# 3. Helper: image parsing
# ---------------------
def parse_base64_image(data_url):
    """
    Convert data URI "data:<mime>;base64,<data>" to dict with binary and mime.
    """
    if not data_url:
        return None
    try:
        header, b64data = data_url.split(',', 1)
        mime = header.split(';')[0].split(':')[1]
        return {'data': Binary(base64.b64decode(b64data)), 'contentType': mime}
    except Exception:
        return None

# ---------------------
# 4. Routes: Static
# ---------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # serve index.html at root and any other static file
    if path == '' or not os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', 'index.html')
    return send_from_directory('public', path)

# ---------------------
# 5. Routes: API
# ---------------------
@app.route('/get-users', methods=['GET'])
def get_users():
    docs = []
    for u in users_col.find():
        item = {
            'id': u.get('id'),
            'name': u.get('name'),
            'age': u.get('age'),
            'occupation': u.get('occupation'),
            'address': u.get('address'),
            'contact': u.get('contact'),
            'idNumber': u.get('idNumber'),
            'documentNumber': u.get('documentNumber'),
            'notarySrNo': u.get('notarySrNo'),
            'documentType': u.get('documentType'),
            'executingParties': u.get('executingParties'),
            'propertyAddress': u.get('propertyAddress'),
            'propertyValue': u.get('propertyValue')
        }
        # attach base64 images if present
        if u.get('photo'):
            item['photoData'] = f"data:{u['photo']['contentType']};base64," + base64.b64encode(u['photo']['data']).decode()
        if u.get('thumbImg'):
            item['thumbData'] = f"data:{u['thumbImg']['contentType']};base64," + base64.b64encode(u['thumbImg']['data']).decode()
        docs.append(item)
    return jsonify(docs)

@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json(force=True)
    # parse images
    photo = parse_base64_image(data.get('photoData', ''))
    thumb = parse_base64_image(data.get('thumbData', ''))
    # build document
    doc = {
        'id': data.get('id'),
        'name': data.get('name'),
        'age': data.get('age'),
        'occupation': data.get('occupation'),
        'address': data.get('address'),
        'contact': data.get('contact'),
        'idNumber': data.get('idNumber'),
        'photo': photo,
        'thumbImg': thumb,
        'documentNumber': data.get('documentNumber'),
        'notarySrNo': data.get('notarySrNo'),
        'documentType': data.get('documentType'),
        'executingParties': data.get('executingParties'),
        'propertyAddress': data.get('propertyAddress'),
        'propertyValue': data.get('propertyValue')
    }
    users_col.insert_one(doc)
    return jsonify({'message': '✅ User added successfully'})

@app.route('/update-user', methods=['POST'])
def update_user():
    data = request.get_json(force=True)
    photo = parse_base64_image(data.get('photoData', ''))
    thumb = parse_base64_image(data.get('thumbData', ''))
    update_fields = {k: data[k] for k in [
        'name','age','occupation','address','contact','idNumber',
        'documentNumber','notarySrNo','documentType','executingParties',
        'propertyAddress','propertyValue'
    ] if data.get(k) is not None}
    if photo: update_fields['photo'] = photo
    if thumb: update_fields['thumbImg'] = thumb
    result = users_col.update_one({'id': data.get('id')}, {'$set': update_fields})
    if result.matched_count:
        return jsonify({'message': '✏️ User updated successfully'})
    abort(404, description='❌ User not found')

@app.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json(force=True)
    result = users_col.delete_one({'id': data.get('id')})
    if result.deleted_count:
        return jsonify({'message': '🗑️ User deleted successfully'})
    abort(404, description='❌ User not found')

# ---------------------
# 6. Run server
# ---------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
