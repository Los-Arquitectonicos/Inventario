const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, enum: ['admin', 'bodeguero', 'vendedor'], required: true },
  notifications: [
    {
      message: { type: String, required: true },
      read: { type: Boolean, default: false },
      timestamp: { type: Date, default: Date.now }
    }
  ]
});

module.exports = mongoose.model('User', UserSchema);
