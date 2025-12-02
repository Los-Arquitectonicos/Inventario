require('dotenv').config();
const app = require('./src/app');

const PORT = process.env.PORT || 3001;
const HOST = process.env.HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
  console.log(`🚀 Notifications Service started on ${HOST}:${PORT}`);
  console.log(`📊 Health check: http://${HOST}:${PORT}/health`);
  console.log(`🔔 API endpoint: http://${HOST}:${PORT}/api/notifications`);
  console.log(`🍃 MongoDB URI: ${process.env.MONGO_URI || 'Not configured'}`);
  console.log(`🔑 JWT Secret: ${process.env.JWT_SECRET ? 'Configured' : 'Not configured'}`);
});
