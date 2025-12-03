const express = require('express');
const cors = require('cors');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Simple health check
app.get('/health', (req, res) => {
  console.log(`[${new Date().toISOString()}] Health check requested`);
  res.status(200).json({ 
    status: 'healthy', 
    service: 'notifications-simple',
    timestamp: new Date().toISOString(),
    message: 'Routing test successful - notifications service is working!'
  });
});

// Root endpoint  
app.get('/', (req, res) => {
  console.log(`[${new Date().toISOString()}] Root endpoint requested`);
  res.json({ 
    message: 'ProvesiWMS Notifications Service - Simplified', 
    version: '1.0.0-simple',
    status: 'success',
    available_endpoints: ['/', '/health', '/test']
  });
});

// Test endpoint
app.get('/test', (req, res) => {
  console.log(`[${new Date().toISOString()}] Test endpoint requested`);
  res.json({ 
    status: 'success',
    message: 'Test successful! Notifications service routing is working.',
    timestamp: new Date().toISOString(),
    service: 'notifications-simple'
  });
});

// 404 handler
app.use('*', (req, res) => {
  console.log(`[${new Date().toISOString()}] 404 - Path not found: ${req.originalUrl}`);
  res.status(404).json({ 
    error: 'Not Found', 
    path: req.originalUrl,
    available_endpoints: ['/', '/health', '/test']
  });
});

const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`🚀 Simple Notifications Service started`);
  console.log(`📍 Listening on: ${HOST}:${PORT}`);
  console.log(`📊 Health: http://localhost:${PORT}/health`);
  console.log(`🧪 Test: http://localhost:${PORT}/test`);
  console.log(`🏠 Root: http://localhost:${PORT}/`);
  console.log(`✅ Ready for testing!`);
});

module.exports = app;