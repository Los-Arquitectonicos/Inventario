const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');

const app = express();

// Connect Database
connectDB();

// Init Middleware
app.use(cors());
app.use(express.json({ extended: false }));

// Health check endpoint for ALB
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({ message: 'ProvesiWMS Notifications Service', version: '1.0.0' });
});

// Define Routes
app.use('/api/auth', require('./routes/authRoutes'));
app.use('/api/notifications', require('./routes/notificationRoutes'));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal Server Error', message: err.message });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.originalUrl });
});

module.exports = app;
