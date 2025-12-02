const express = require('express');
const router = express.Router();
const notificationController = require('../controllers/notificationController');
const auth = require('../middleware/authMiddleware');

router.post('/', auth, notificationController.createNotification);
router.get('/', auth, notificationController.getNotifications);
router.put('/:id/read', auth, notificationController.markRead);
router.delete('/:id', auth, notificationController.deleteNotification);

module.exports = router;
