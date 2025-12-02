#!/usr/bin/env node
/**
 * Setup script for Notifications Service
 * Creates default users and configuration
 */

const mongoose = require('mongoose');
const User = require('./src/models/User');
const bcrypt = require('bcryptjs');

// Default users to create
const defaultUsers = [
  {
    email: 'admin@provesi.com',
    username: 'admin',
    firstName: 'System',
    lastName: 'Administrator',
    role: 'admin',
    password: 'Admin123!',
    isActive: true,
    isEmailVerified: true
  },
  {
    email: 'manager@provesi.com',
    username: 'manager',
    firstName: 'Warehouse',
    lastName: 'Manager',
    role: 'manager',
    password: 'Manager123!',
    isActive: true,
    isEmailVerified: true
  },
  {
    email: 'user@provesi.com',
    username: 'testuser',
    firstName: 'Test',
    lastName: 'User',
    role: 'user',
    password: 'User123!',
    isActive: true,
    isEmailVerified: true
  }
];

async function setupDatabase() {
  try {
    console.log('🔧 Setting up Notifications Service database...');
    
    // Connect to MongoDB
    const mongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017/notifications';
    await mongoose.connect(mongoUri);
    console.log('✅ Connected to MongoDB');

    // Clear existing users (optional - remove if you want to keep existing)
    const existingUsersCount = await User.countDocuments();
    console.log(`📊 Found ${existingUsersCount} existing users`);

    // Create default users
    console.log('👤 Creating default users...');
    
    for (const userData of defaultUsers) {
      try {
        // Check if user already exists
        const existingUser = await User.findOne({ 
          $or: [
            { email: userData.email },
            { username: userData.username }
          ]
        });

        if (existingUser) {
          console.log(`⚠️  User ${userData.email} already exists, skipping...`);
          continue;
        }

        // Hash password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(userData.password, salt);

        // Create user
        const user = new User({
          ...userData,
          password: hashedPassword
        });

        await user.save();
        console.log(`✅ Created user: ${userData.email} (${userData.role})`);
        
      } catch (userError) {
        console.error(`❌ Error creating user ${userData.email}:`, userError.message);
      }
    }

    // Display final summary
    const totalUsers = await User.countDocuments();
    const adminUsers = await User.countDocuments({ role: 'admin' });
    const managerUsers = await User.countDocuments({ role: 'manager' });
    const regularUsers = await User.countDocuments({ role: 'user' });

    console.log('\n📋 Database Setup Complete!');
    console.log('═══════════════════════════════');
    console.log(`Total users: ${totalUsers}`);
    console.log(`Admins: ${adminUsers}`);
    console.log(`Managers: ${managerUsers}`);
    console.log(`Users: ${regularUsers}`);
    
    console.log('\n🔑 Default Login Credentials:');
    console.log('═══════════════════════════════');
    defaultUsers.forEach(user => {
      console.log(`${user.role.toUpperCase()}: ${user.email} / ${user.password}`);
    });

    console.log('\n🚀 Service is ready to use!');
    console.log('API Base URL: http://your-ec2-ip:3001');
    console.log('Health Check: http://your-ec2-ip:3001/health');

  } catch (error) {
    console.error('❌ Setup failed:', error);
    process.exit(1);
  } finally {
    await mongoose.connection.close();
    console.log('🔌 Database connection closed');
  }
}

// Show usage information
function showUsage() {
  console.log('\n📖 Notifications Service Setup');
  console.log('═══════════════════════════════');
  console.log('This script sets up the notifications service with default users.');
  console.log('\nUsage:');
  console.log('  node setup.js');
  console.log('\nEnvironment Variables:');
  console.log('  MONGO_URI - MongoDB connection string (default: mongodb://localhost:27017/notifications)');
  console.log('\nDefault Users Created:');
  console.log('  - admin@provesi.com (Admin)');
  console.log('  - manager@provesi.com (Manager)');
  console.log('  - user@provesi.com (Regular User)');
  console.log('\nAfter setup, you can:');
  console.log('  1. Start the service: npm start');
  console.log('  2. Test authentication: POST /auth/login');
  console.log('  3. Create notifications: POST /notifications');
  console.log('  4. Send emails: POST /notifications with sendEmail: true');
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  showUsage();
  process.exit(0);
}

// Run setup
setupDatabase();