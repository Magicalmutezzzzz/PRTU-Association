// server.js
const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB Atlas
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('✅ Connected to MongoDB Atlas'))
.catch(err => console.error('❌ MongoDB connection error:', err));

// User schema with image buffers
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

// Middleware
app.use(express.json({ limit: '20mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// Helper: base64 data URI -> buffer & contentType
function parseBase64Image(dataURL) {
  const matches = dataURL.match(/^data:(.+);base64,(.+)$/);
  if (!matches) return null;
  return {
    contentType: matches[1],
    data: Buffer.from(matches[2], 'base64')
  };
}

// GET all users
app.get('/get-users', async (req, res) => {
  try {
    const users = await User.find();
    const safe = users.map(u => {
      const obj = u.toObject();
      if (u.photo && u.photo.data) {
        obj.photoData = `data:${u.photo.contentType};base64,${u.photo.data.toString('base64')}`;
      }
      if (u.thumbImg && u.thumbImg.data) {
        obj.thumbData = `data:${u.thumbImg.contentType};base64,${u.thumbImg.data.toString('base64')}`;
      }
      delete obj.photo;
      delete obj.thumbImg;
      return obj;
    });
    res.json(safe);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '❌ Failed to fetch users' });
  }
});

// POST add user
app.post('/add-user', async (req, res) => {
  try {
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
    console.error(err);
    res.status(500).json({ error: '❌ Failed to add user' });
  }
});

// POST update user
app.post('/update-user', async (req, res) => {
  try {
    const photoParsed = parseBase64Image(req.body.photoData || '');
    const thumbParsed = parseBase64Image(req.body.thumbData || '');
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
    console.error(err);
    res.status(500).json({ error: '❌ Failed to update user' });
  }
});

// POST delete user
app.post('/delete-user', async (req, res) => {
  try {
    const del = await User.findOneAndDelete({ id: req.body.id });
    if (del) res.json({ message: '🗑️ User deleted successfully' });
    else res.status(404).json({ message: '❌ User not found' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '❌ Failed to delete user' });
  }
});

// Serve landing page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));
