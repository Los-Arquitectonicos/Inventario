const express = require('express');
const cors = require('cors');

const app = express();

// Init Middleware
app.use(cors());
app.use(express.json({ extended: false }));

// Health check endpoint for ALB
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    service: 'notifications-simple',
    timestamp: new Date().toISOString(),
    message: 'Simple notifications service for testing routing'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({ 
    message: 'ProvesiWMS Notifications Service - Simplified for Testing', 
    version: '1.0.0-simple',
    status: 'success',
    endpoints: ['/health', '/', '/test']
  });
});

// Simple test endpoint
app.get('/test', (req, res) => {
  res.json({ 
    status: 'success',
    message: 'Notifications routing test successful!',
    timestamp: new Date().toISOString(),
    request_info: {
      method: req.method,
      path: req.path,
      ip: req.ip,
      headers: req.headers
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ 
    error: 'Not Found', 
    path: req.originalUrl,
    message: 'Available endpoints: /, /health, /test'
  });
});

module.exports = app;
