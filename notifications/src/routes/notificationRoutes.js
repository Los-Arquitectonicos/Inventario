const express = require('express');
const router = express.Router();
const notificationController = require('../controllers/notificationController');
const auth = require('../middleware/authMiddleware');

// Create notification (admin and manager can send notifications)
router.post('/', auth, notificationController.createNotification);

// Get notifications (paginated, filtered)
router.get('/', auth, notificationController.getNotifications);

// Mark notification as read
router.patch('/:id/read', auth, notificationController.markRead);
router.put('/:id/read', auth, notificationController.markRead);

// Delete notification
router.delete('/:id', auth, notificationController.deleteNotification);

module.exports = router;
