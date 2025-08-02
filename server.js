// server.js
// Entry point for PRTU dashboard backend: sets up Express, connects to MongoDB Atlas, and defines CRUD routes.

// ---------------------
// Module imports & config
// ---------------------
const express = require('express');            // Web framework
const mongoose = require('mongoose');          // MongoDB ODM
const path = require('path');                  // Utility for file paths
require('dotenv').config();                    // Load env vars from .env

// ---------------------
// App initialization
// ---------------------
const app = express();                         // Create Express app
const PORT = process.env.PORT || 3000;         // Use env PORT or fallback to 3000

// ---------------------
// Middleware
// ---------------------
// 1. Parse JSON bodies (requests with Content-Type: application/json)
app.use(express.json({ limit: '20mb' }));
// 2. Parse URL-encoded bodies (forms, Content-Type: application/x-www-form-urlencoded)
app.use(express.urlencoded({ extended: true, limit: '20mb' }));
// 3. Serve static assets from "public" folder (HTML/CSS/JS)
app.use(express.static(path.join(__dirname, 'public')));

// ---------------------
// Database connection
// ---------------------
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('✅ Connected to MongoDB Atlas'))
.catch(err => console.error('❌ MongoDB connection error:', err));

// ---------------------
// Mongoose schema & model
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
// Helper: parse base64 image data
// ---------------------
function parseBase64Image(dataURL) {
  // Expect format: "data:<mime>;base64,<data>"
  const matches = dataURL.match(/^data:(.+);base64,(.+)$/);
  if (!matches) return null; // return null if not a valid data URI
  return {
    contentType: matches[1],
    data: Buffer.from(matches[2], 'base64')
  };
}

// ---------------------
// Routes
// ---------------------

// GET /get-users
// Fetch all users from DB, convert image buffers back to base64 strings, and return JSON
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

// POST /add-user
// Create a new user document from req.body data
app.post('/add-user', async (req, res) => {
  try {
    console.log('🔍 [add-user] request body:', req.body);
    const photoParsed = parseBase64Image(req.body.photoData || '');
    const thumbParsed = parseBase64Image(req.body.thumbData || '');

    const newUser = new User({
      id: req.body.id,
      name: req.body.name,
      age: req.body.age,
      occupation: req.body.occupation,
      address: req.body.address,
      contact: req.body.contact,
      idNumber: req.body.idNumber,
      photo: photoParsed,
      thumbImg: thumbParsed,
      documentNumber: req.body.documentNumber,
      notarySrNo: req.body.notarySrNo,
      documentType: req.body.documentType,
      executingParties: req.body.executingParties,
      propertyAddress: req.body.propertyAddress,
      propertyValue: req.body.propertyValue
    });

    await newUser.save();
    res.json({ message: '✅ User added successfully' });
  } catch (err) {
    console.error('Error adding user:', err);
    res.status(500).json({ error: '❌ Failed to add user' });
  }
});

// POST /update-user
// Update an existing user by id with fields provided in req.body
app.post('/update-user', async (req, res) => {
  try {
    console.log('🔍 [update-user] request body:', req.body);
    const photoParsed = parseBase64Image(req.body.photoData || '');
    const thumbParsed = parseBase64Image(req.body.thumbData || '');

    // Prepare update fields
    const fields = {
      name: req.body.name,
      age: req.body.age,
      occupation: req.body.occupation,
      address: req.body.address,
      contact: req.body.contact,
      idNumber: req.body.idNumber,
      documentNumber: req.body.documentNumber,
      notarySrNo: req.body.notarySrNo,
      documentType: req.body.documentType,
      executingParties: req.body.executingParties,
      propertyAddress: req.body.propertyAddress,
      propertyValue: req.body.propertyValue
    };
    if (photoParsed) fields.photo = photoParsed;
    if (thumbParsed) fields.thumbImg = thumbParsed;

    const updated = await User.findOneAndUpdate({ id: req.body.id }, fields, { new: true });
    if (updated) res.json({ message: '✏️ User updated successfully' });
    else res.status(404).json({ message: '❌ User not found' });
  } catch (err) {
    console.error('Error updating user:', err);
    res.status(500).json({ error: '❌ Failed to update user' });
  }
});

// POST /delete-user
// Remove a user document matching req.body.id
app.post('/delete-user', async (req, res) => {
  try {
    console.log('🔍 [delete-user] request body:', req.body);
    const deleted = await User.findOneAndDelete({ id: req.body.id });
    if (deleted) res.json({ message: '🗑️ User deleted successfully' });
    else res.status(404).json({ message: '❌ User not found' });
  } catch (err) {
    console.error('Error deleting user:', err);
    res.status(500).json({ error: '❌ Failed to delete user' });
  }
});

// ---------------------
// Serve front-end
// ---------------------
app.get('/', (req, res) => {
  // Send the HTML file for your dashboard UI
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ---------------------
// Start server
// ---------------------
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));
