import os, base64
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_pymongo import PyMongo
from bson.binary import Binary
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment
load_dotenv()
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASS = os.getenv('MONGO_PASS')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_DB   = os.getenv('MONGO_DB','prtuDB')
if not all([MONGO_USER, MONGO_PASS, MONGO_HOST]):
    raise RuntimeError("❌ Set MONGO_USER, MONGO_PASS, MONGO_HOST!")

# Build URI
user_q = quote_plus(MONGO_USER)
pass_q = quote_plus(MONGO_PASS)
MONGO_URI = f"mongodb+srv://{user_q}:{pass_q}@{MONGO_HOST}/{MONGO_DB}?retryWrites=true&w=majority"

# Init
app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MONGO_URI'] = MONGO_URI
mongo = PyMongo(app)
db = mongo.db

def parse_base64_image(data_url):
    if not data_url: return None
    try:
        header, b64 = data_url.split(',',1)
        mime = header.split(';')[0].split(':')[1]
        return {'data':Binary(base64.b64decode(b64)), 'contentType':mime}
    except:
        return None

# Serve frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    fp = os.path.join('public', path)
    if path and os.path.exists(fp):
        return send_from_directory('public', path)
    return send_from_directory('public', 'index.html')

# Get all
@app.route('/get-users', methods=['GET'])
def get_users():
    items = []
    for r in db.users.find():
        doc = {}
        for k in [
            'id','metaDocumentNumber','metaNotarySrNo','metaDocumentType',
            'scheduleOfProperty','consideration',
            'purchaserName','purchaserAge','purchaserOccupation','purchaserAddress','purchaserContact','purchaserIdNumber',
            'sellerName','sellerAge','sellerOccupation','sellerAddress','sellerContact','sellerIdNumber',
            'witnessName','witnessAge','witnessOccupation','witnessAddress','witnessContact','witnessIdNumber'
        ]:
            if k in r: doc[k] = r[k]
        for field in ['photoP','photoS','photoW','thumbP','thumbS','thumbW']:
            img = r.get(field)
            if img and img.get('data'):
                b64 = base64.b64encode(img['data']).decode()
                doc[field] = f"data:{img['contentType']};base64,{b64}"
        items.append(doc)
    return jsonify(items)

# Add
@app.route('/add-user', methods=['POST'])
def add_user():
    d = request.get_json(force=True)
    rec = {k: d.get(k) for k in d if not k.endswith(('P','S','W'))}
    for img in ['photoP','photoS','photoW','thumbP','thumbS','thumbW']:
        parsed = parse_base64_image(d.get(img))
        if parsed: rec[img] = parsed
    db.users.insert_one(rec)
    return jsonify({'message':'✅ Document added successfully'})

# Update
@app.route('/update-user', methods=['POST'])
def update_user():
    d = request.get_json(force=True)
    upd = {k: d[k] for k in d if not k.endswith(('P','S','W'))}
    for img in ['photoP','photoS','photoW','thumbP','thumbS','thumbW']:
        parsed = parse_base64_image(d.get(img))
        if parsed: upd[img] = parsed
    res = db.users.update_one({'id':d.get('id')},{'$set':upd})
    if res.matched_count:
        return jsonify({'message':'✏️ Document updated successfully'})
    abort(404,'❌ Document not found')

# Delete
@app.route('/delete-user', methods=['POST'])
def delete_user():
    d = request.get_json(force=True)
    res = db.users.delete_one({'id':d.get('id')})
    if res.deleted_count:
        return jsonify({'message':'🗑️ Document deleted successfully'})
    abort(404,'❌ Document not found')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT',3000)))
