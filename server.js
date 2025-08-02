// server.js
// Backend for PRTU dashboard: Express + MongoDB Atlas

// ---------------------
// 1. Module imports & config
// ---------------------
const express = require('express');            // Web framework
const mongoose = require('mongoose');          // MongoDB ODM
const path = require('path');                  // File path utils
require('dotenv').config();                    // Load .env variables

// ---------------------
// 2. App initialization
// ---------------------
const app = express();                         // Create Express app
const PORT = process.env.PORT || 3000;         // Port from env or default

// ---------------------
// 3. Middleware setup
// ---------------------

// 3.1. Parse JSON bodies (Content-Type: application/json)
app.use(express.json({ limit: '20mb' }));
// 3.2. Parse URL-encoded bodies (forms)
app.use(express.urlencoded({ extended: true, limit: '20mb' }));
// 3.3. Serve static assets (front-end files)
app.use(express.static(path.join(__dirname, 'public')));

// 3.4. Capture raw request body (string) for debugging/fallback parsing
// This runs before any route. Always provides req.rawBody as a string.
app.use((req, res, next) => {
  let data = '';
  req.setEncoding('utf8');
  req.on('data', chunk => { data += chunk; });
  req.on('end', () => {
    req.rawBody = data;
    next();
  });
});

// ---------------------
// 4. Database connection
// ---------------------
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('✅ Connected to MongoDB Atlas'))
.catch(err => console.error('❌ MongoDB connection error:', err));

// ---------------------
// 5. Mongoose schema & model
// ---------------------
const userSchema = new mongoose.Schema({
  id: Number,
  name: String,
  age: String,
  occupation: String,
  address: String,
  contact: String,
  idNumber: String,
  photo: {
    data: Buffer,
    contentType: String
  },
  thumbImg: {
    data: Buffer,
    contentType: String
  },
  documentNumber: String,
  notarySrNo: String,
  documentType: String,
  executingParties: String,
  propertyAddress: String,
  propertyValue: String
});
const User = mongoose.model('User', userSchema);

// ---------------------
// 6. Helper: parse base64 image data URI
// ---------------------
function parseBase64Image(dataURL) {
  // Example dataURL: "data:image/jpeg;base64,/9j/4AAQ..."
  const matches = dataURL.match(/^data:(.+);base64,(.+)$/);
  if (!matches) return null;
  return {
    contentType: matches[1],
    data: Buffer.from(matches[2], 'base64')
  };
}

// ---------------------
// 7. Route handlers
// ---------------------

// Utility to get parsed body: prefers express-parsed req.body, falls back to rawBody
function getParsedBody(req) {
  if (req.body && Object.keys(req.body).length) {
    return req.body;
  }
  try {
    return JSON.parse(req.rawBody || '{}');
  } catch (e) {
    console.warn('Could not parse rawBody:', req.rawBody);
    return {};
  }
}

// 7.1. GET /get-users
// Fetch users, convert image buffers to base64 data URIs
app.get('/get-users', async (req, res) => {
  try {
    const users = await User.find();
    const safe = users.map(u => {
      const obj = u.toObject();
      if (u.photo?.data) {
        obj.photoData = `data:${u.photo.contentType};base64,${u.photo.data.toString('base64')}`;
      }
      if (u.thumbImg?.data) {
        obj.thumbData = `data:${u.thumbImg.contentType};base64,${u.thumbImg.data.toString('base64')}`;
      }
      delete obj.photo;
      delete obj.thumbImg;
      return obj;
    });
    res.json(safe);
  } catch (err) {
    console.error('Error fetching users:', err);
    res.status(500).json({ error: '❌ Failed to fetch users' });
  }
});

// 7.2. POST /add-user
// Create user from parsed body. Logs headers, parsed & raw bodies.
app.post('/add-user', async (req, res) => {
  const parsed = getParsedBody(req);
  console.log('Headers:', req.headers['content-type']);
  console.log('Parsed body:', parsed);
  console.log('Raw body:', req.rawBody);
  try {
    const photoParsed = parseBase64Image(parsed.photoData || '');
    const thumbParsed = parseBase64Image(parsed.thumbData || '');
    const newUser = new User({
      id: parsed.id,
      name: parsed.name,
      age: parsed.age,
      occupation: parsed.occupation,
      address: parsed.address,
      contact: parsed.contact,
      idNumber: parsed.idNumber,
      photo: photoParsed,
      thumbImg: thumbParsed,
      documentNumber: parsed.documentNumber,
      notarySrNo: parsed.notarySrNo,
      documentType: parsed.documentType,
      executingParties: parsed.executingParties,
      propertyAddress: parsed.propertyAddress,
      propertyValue: parsed.propertyValue
    });
    await newUser.save();
    res.json({ message: '✅ User added successfully' });
  } catch (err) {
    console.error('Error adding user:', err);
    res.status(500).json({ error: '❌ Failed to add user' });
  }
});

// 7.3. POST /update-user
// Similar to add-user but updates existing by id
app.post('/update-user', async (req, res) => {
  const parsed = getParsedBody(req);
  console.log('Headers:', req.headers['content-type']);
  console.log('Parsed body:', parsed);
  try {
    const photoParsed = parseBase64Image(parsed.photoData || '');
    const thumbParsed = parseBase64Image(parsed.thumbData || '');
    const fields = {
      name: parsed.name,
      age: parsed.age,
      occupation: parsed.occupation,
      address: parsed.address,
      contact: parsed.contact,
      idNumber: parsed.idNumber,
      documentNumber: parsed.documentNumber,
      notarySrNo: parsed.notarySrNo,
      documentType: parsed.documentType,
      executingParties: parsed.executingParties,
      propertyAddress: parsed.propertyAddress,
      propertyValue: parsed.propertyValue
    };
    if (photoParsed) fields.photo = photoParsed;
    if (thumbParsed) fields.thumbImg = thumbParsed;
    const updated = await User.findOneAndUpdate({ id: parsed.id }, fields, { new: true });
    if (updated) res.json({ message: '✏️ User updated successfully' });
    else res.status(404).json({ message: '❌ User not found' });
  } catch (err) {
    console.error('Error updating user:', err);
    res.status(500).json({ error: '❌ Failed to update user' });
  }
});

// 7.4. POST /delete-user
app.post('/delete-user', async (req, res) => {
  const parsed = getParsedBody(req);
  console.log('Headers:', req.headers['content-type']);
  console.log('Parsed body:', parsed);
  try {
    const deleted = await User.findOneAndDelete({ id: parsed.id });
    if (deleted) res.json({ message: '🗑️ User deleted successfully' });
    else res.status(404).json({ message: '❌ User not found' });
  } catch (err) {
    console.error('Error deleting user:', err);
    res.status(500).json({ error: '❌ Failed to delete user' });
  }
});

// ---------------------
// 8. Serve front-end
// ---------------------
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ---------------------
// 9. Start server
// ---------------------
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));

/*
Explanation:
1) express.json() & express.urlencoded() ensure req.body is parsed if the client sets Content-Type correctly.
2) We capture the raw body string in req.rawBody to debug and as fallback parsing.
3) getParsedBody() picks the JSON-parsed body or attempts JSON.parse on rawBody.
4) In each POST route we log:
   - req.headers['content-type'] (to verify the client is sending the right header)
   - parsed body object
   - raw body string
5) After deployment, inspect these logs in Render. If parsed body is still empty,
   check your front-end fetch or form submission: you *must* include:
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(yourDataObject)
6) These logs will pinpoint whether the data ever leaves the client, and what the server actually receives.
*/
