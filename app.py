# app.py
"""
Flask backend for PRTU Sale Deed dashboard:
- Serves static frontend from /public
- Provides CRUD for documents in MongoDB Atlas
- Safely encodes credentials per RFC 3986
- Stores all fields including metadata, purchaser/seller/witness details and images
"""
import os
import base64
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_pymongo import PyMongo
from bson.binary import Binary
from dotenv import load_dotenv
from urllib.parse import quote_plus

# 1. Load environment vars
load_dotenv()
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')  # e.g. cluster0.abcd.mongodb.net
MONGO_DB   = os.getenv('MONGO_DB', 'prtuDB')
if not all([MONGO_USER, MONGO_PASS, MONGO_HOST]):
    raise RuntimeError("❌ Please set MONGO_USER, MONGO_PASS, and MONGO_HOST in your environment.")

# Quote special chars
user_q = quote_plus(MONGO_USER)
pass_q = quote_plus(MONGO_PASS)
MONGO_URI = (
    f"mongodb+srv://{user_q}:{pass_q}@{MONGO_HOST}/{MONGO_DB}?retryWrites=true&w=majority"
)

# 2. Initialize app
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)
db = mongo.db

# 3. Helper: parse base64 image data
def parse_base64_image(data_url):
    if not data_url:
        return None
    try:
        header, b64 = data_url.split(',',1)
        mime = header.split(';')[0].split(':')[1]
        return { 'data': Binary(base64.b64decode(b64)), 'contentType': mime }
    except:
        return None

# 4. Serve static
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', path)
    return send_from_directory('public', 'index.html')

# 5. API: Get all documents
@app.route('/get-users', methods=['GET'])
def get_users():
    docs = []
    for rec in db.users.find():
        # Build JSON-friendly dict
        item = {}
        # List all scalar fields
        for k in [
            'id', 'metaDocumentNumber', 'metaNotarySrNo', 'metaDocumentType',
            'scheduleOfProperty', 'consideration',
            'purchaserName','purchaserAge','purchaserOccupation','purchaserAddress','purchaserContact','purchaserIdNumber',
            'sellerName','sellerAge','sellerOccupation','sellerAddress','sellerContact','sellerIdNumber',
            'witnessName','witnessAge','witnessOccupation','witnessAddress','witnessContact','witnessIdNumber'
        ]:
            if rec.get(k) is not None:
                item[k] = rec[k]
        # Images: photoP, photoS, photoW
        for img_field in ['photoP','photoS','photoW']:
            img = rec.get(img_field)
            if img and img.get('data'):
                item[img_field] = f"data:{img['contentType']};base64," + base64.b64encode(img['data']).decode()
        # Thumbs
        for t_field in ['thumbP','thumbS','thumbW']:
            thumb = rec.get(t_field)
            if thumb and thumb.get('data'):
                item[t_field] = f"data:{thumb['contentType']};base64," + base64.b64encode(thumb['data']).decode()
        docs.append(item)
    return jsonify(docs)

# 6. API: Add new document
@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json(force=True)
    # Parse images
    photoP = parse_base64_image(data.get('photoP'))
    photoS = parse_base64_image(data.get('photoS'))
    photoW = parse_base64_image(data.get('photoW'))
    thumbP = parse_base64_image(data.get('thumbP'))
    thumbS = parse_base64_image(data.get('thumbS'))
    thumbW = parse_base64_image(data.get('thumbW'))
    # Build record
    rec = {
        # IDs & metadata
        'id': data.get('id'),
        'metaDocumentNumber': data.get('metaDocumentNumber'),
        'metaNotarySrNo': data.get('metaNotarySrNo'),
        'metaDocumentType': data.get('metaDocumentType'),
        'scheduleOfProperty': data.get('scheduleOfProperty'),
        'consideration': data.get('consideration'),
        # Parties
        'purchaserName': data.get('purchaserName'), 'purchaserAge': data.get('purchaserAge'),
        'purchaserOccupation': data.get('purchaserOccupation'), 'purchaserAddress': data.get('purchaserAddress'),
        'purchaserContact': data.get('purchaserContact'), 'purchaserIdNumber': data.get('purchaserIdNumber'),
        'sellerName': data.get('sellerName'), 'sellerAge': data.get('sellerAge'),
        'sellerOccupation': data.get('sellerOccupation'), 'sellerAddress': data.get('sellerAddress'),
        'sellerContact': data.get('sellerContact'), 'sellerIdNumber': data.get('sellerIdNumber'),
        'witnessName': data.get('witnessName'), 'witnessAge': data.get('witnessAge'),
        'witnessOccupation': data.get('witnessOccupation'), 'witnessAddress': data.get('witnessAddress'),
        'witnessContact': data.get('witnessContact'), 'witnessIdNumber': data.get('witnessIdNumber'),
        # Images
        'photoP': photoP, 'photoS': photoS, 'photoW': photoW,
        'thumbP': thumbP, 'thumbS': thumbS, 'thumbW': thumbW
    }
    db.users.insert_one(rec)
    return jsonify({'message':'✅ Document added successfully'})

# 7. API: Update existing document
@app.route('/update-user', methods=['POST'])
def update_user():
    data = request.get_json(force=True)
    update = {}
    # Scalar fields
    for k in [
        'metaDocumentNumber','metaNotarySrNo','metaDocumentType','scheduleOfProperty','consideration',
        'purchaserName','purchaserAge','purchaserOccupation','purchaserAddress','purchaserContact','purchaserIdNumber',
        'sellerName','sellerAge','sellerOccupation','sellerAddress','sellerContact','sellerIdNumber',
        'witnessName','witnessAge','witnessOccupation','witnessAddress','witnessContact','witnessIdNumber'
    ]:
        if k in data:
            update[k] = data[k]
    # Images
    for img in ['photoP','photoS','photoW']:
        parsed = parse_base64_image(data.get(img))
        if parsed: update[img] = parsed
    for tm in ['thumbP','thumbS','thumbW']:
        parsed = parse_base64_image(data.get(tm))
        if parsed: update[tm] = parsed
    result = db.users.update_one({'id': data.get('id')}, {'$set': update})
    if result.matched_count:
        return jsonify({'message':'✏️ Document updated successfully'})
    abort(404, description='❌ Document not found')

# 8. API: Delete document
@app.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json(force=True)
    result = db.users.delete_one({'id': data.get('id')})
    if result.deleted_count:
        return jsonify({'message':'🗑️ Document deleted successfully'})
    abort(404, description='❌ Document not found')

# 9. Run
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
