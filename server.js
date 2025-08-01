// ==========================
// 📦 Dependencies & Config
// ==========================
const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
const app = express();
const PORT = 3000;
require('dotenv').config();

// ==========================
// 🌐 MongoDB Connection
// ==========================
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("✅ Connected to MongoDB Atlas"))
  .catch(err => console.error("❌ MongoDB connection error:", err));

// ==========================
// 🧬 User Schema (includes image binary)
// ==========================
const userSchema = new mongoose.Schema({
  id: Number,
  name: String,
  age: String,
  occupation: String,
  address: String,
  contact: String,
  idNumber: String,

  photo: {
     Buffer,
    contentType: String
  },
  thumbImg: {
     Buffer,
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

// ==========================
// 🔧 Middleware
// ==========================
app.use(express.json({ limit: '20mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ==========================
// ♻️ Helpers: Base64 to Buffer
// ==========================
function parseBase64Image(dataURL) {
  const matches = dataURL.match(/^(.+);base64,(.+)$/);
  if (!matches) return null;
  return {
    contentType: matches[1],
    buffer: Buffer.from(matches[2], 'base64')
  };
}

// ==========================
// 📡 API Routes
// ==========================

// 🧾 GET all users
app.get('/get-users', async (req, res) => {
  try {
    const users = await User.find();

    // 🔁 Convert binary photo/fingerprint back to data URI
    const safeUsers = users.map(user => {
      const copy = user.toObject();
      if (user.photo?.data) {
        copy.photoData = `${user.photo.contentType};base64,${user.photo.data.toString('base64')}`;
      }
      if (user.thumbImg?.data) {
        copy.thumbData = `${user.thumbImg.contentType};base64,${user.thumbImg.data.toString('base64')}`;
      }
      delete copy.photo;
      delete copy.thumbImg;
      return copy;
    });

    res.json(safeUsers);
  } catch (err) {
    res.status(500).json({ error: '❌ Failed to fetch users' });
  }
});

// ➕ POST: Add new user
app.post('/add-user', async (req, res) => {
  try {
    const photoParsed = parseBase64Image(req.body.photoData || '');
    const thumbParsed = parseBase64Image(req.body.thumbData || '');

    const newUser = new User({
      id: req.body.id || Date.now(),
      name: req.body.name || "",
      age: req.body.age || "",
      occupation: req.body.occupation || "",
      address: req.body.address || "",
      contact: req.body.contact || "",
      idNumber: req.body.idNumber || "",

      photo: photoParsed || undefined,
      thumbImg: thumbParsed || undefined,

      documentNumber: req.body.documentNumber || "",
      notarySrNo: req.body.notarySrNo || "",
      documentType: req.body.documentType || "",
      executingParties: req.body.executingParties || "",
      propertyAddress: req.body.propertyAddress || "",
      propertyValue: req.body.propertyValue || ""
    });

    await newUser.save();
    res.json({ message: '✅ User added successfully' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '❌ Failed to add user' });
  }
});

// ✏️ POST: Update user
app.post('/update-user', async (req, res) => {
  try {
    const photoParsed = parseBase64Image(req.body.photoData || '');
    const thumbParsed = parseBase64Image(req.body.thumbData || '');

    const updatedFields = {
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

    if (photoParsed) updatedFields.photo = photoParsed;
    if (thumbParsed) updatedFields.thumbImg = thumbParsed;

    const updated = await User.findOneAndUpdate(
      { id: req.body.id },
      updatedFields,
      { new: true }
    );

    if (updated) {
      res.json({ message: '✏️ User updated successfully' });
    } else {
      res.status(404).json({ message: '❌ User not found' });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '❌ Failed to update user' });
  }
});

// ❌ POST: Delete user
app.post('/delete-user', async (req, res) => {
  try {
    const deleted = await User.findOneAndDelete({ id: req.body.id });
    if (deleted) {
      res.json({ message: '🗑️ User deleted successfully' });
    } else {
      res.status(404).json({ message: '❌ User not found for deletion' });
    }
  } catch (err) {
    res.status(500).json({ error: '❌ Failed to delete user' });
  }
});

// ==========================
// 🌐 Serve Frontend
// ==========================
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ==========================
// 🚀 Start Server
// ==========================
app.listen(PORT, () => {
  console.log(`✅ Server running at: http://localhost:${PORT}`);
});
