const express = require('express');
const cors = require('cors');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Simple health check for ALB and testing
app.get('/health', (req, res) => {
  console.log(`[${new Date().toISOString()}] Health check requested from ${req.ip}`);
  res.status(200).json({ 
    status: 'healthy', 
    service: 'notifications-simple',
    timestamp: new Date().toISOString(),
    message: 'Notifications service is healthy and ready for routing tests'
  });
});

// Root endpoint  
app.get('/', (req, res) => {
  console.log(`[${new Date().toISOString()}] Root endpoint requested from ${req.ip}`);
  res.json({ 
    message: 'ProvesiWMS Notifications Service - Simplified for Testing', 
    version: '1.0.0-simple',
    status: 'success',
    purpose: 'Routing validation for Kong API Gateway',
    available_endpoints: {
      'root': '/',
      'health_check': '/health', 
      'test_endpoint': '/test'
    }
  });
});

// Test endpoint for Kong routing validation
app.get('/test', (req, res) => {
  console.log(`[${new Date().toISOString()}] Test endpoint requested from ${req.ip}`);
  res.json({ 
    status: 'success',
    message: 'Kong routing test successful! Notifications service is receiving requests.',
    timestamp: new Date().toISOString(),
    service: 'notifications-simple',
    route_info: {
      path: req.path,
      method: req.method,
      headers_received: Object.keys(req.headers).length,
      user_agent: req.get('User-Agent') || 'Unknown'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  console.log(`[${new Date().toISOString()}] 404 - Path not found: ${req.originalUrl} from ${req.ip}`);
  res.status(404).json({ 
    error: 'Not Found', 
    path: req.originalUrl,
    message: 'This endpoint does not exist in the simplified notifications service',
    available_endpoints: ['/', '/health', '/test']
  });
});

const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`🚀 Simple Notifications Service for Testing started`);
  console.log(`📍 Listening on: ${HOST}:${PORT}`);
  console.log(`📊 Health check: http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/health`);
  console.log(`🧪 Test endpoint: http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/test`);
  console.log(`🏠 Root endpoint: http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/`);
  console.log(`🎯 Purpose: Kong API Gateway routing validation`);
  console.log(`✅ Ready for infrastructure testing!`);
});

module.exports = app;
