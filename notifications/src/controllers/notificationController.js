const Notification = require('../models/Notification');
const emailService = require('../services/emailService');

const notificationController = {
  // Create a new notification
  async createNotification(req, res) {
    try {
      const { title, message, type, priority, recipientEmail, sendEmail = false } = req.body;
      
      // Validation
      if (!title || !message || !recipientEmail) {
        return res.status(400).json({
          success: false,
          message: 'Title, message, and recipientEmail are required'
        });
      }

      // Create notification
      const notification = new Notification({
        title,
        message,
        type: type || 'info',
        priority: priority || 'medium',
        recipientEmail: recipientEmail.toLowerCase(),
        senderUserId: req.user.id
      });

      await notification.save();

      // Send email if requested
      if (sendEmail) {
        try {
          const emailResult = await emailService.sendNotificationEmail(notification);
          
          if (emailResult.success) {
            notification.emailSent = true;
            notification.emailSentAt = emailResult.sentAt;
          } else {
            notification.emailError = emailResult.error;
          }
          
          await notification.save();
        } catch (emailError) {
          console.error('Email sending failed:', emailError);
          notification.emailError = emailError.message;
          await notification.save();
        }
      }

      res.status(201).json({
        success: true,
        message: 'Notification created successfully',
        notification: {
          id: notification._id,
          title: notification.title,
          message: notification.message,
          type: notification.type,
          priority: notification.priority,
          recipientEmail: notification.recipientEmail,
          isRead: notification.isRead,
          emailSent: notification.emailSent,
          emailSentAt: notification.emailSentAt,
          emailError: notification.emailError,
          createdAt: notification.createdAt
        }
      });

    } catch (error) {
      console.error('Create notification error:', error);
      res.status(500).json({
        success: false,
        message: 'Server error while creating notification'
      });
    }
  },

  // Get notifications
  async getNotifications(req, res) {
    try {
      const { 
        read, 
        type, 
        priority, 
        recipientEmail,
        page = 1, 
        limit = 20 
      } = req.query;

      // Build filter
      const filter = {};
      
      if (read !== undefined) {
        filter.isRead = read === 'true';
      }
      
      if (type) {
        filter.type = type;
      }
      
      if (priority) {
        filter.priority = priority;
      }
      
      if (recipientEmail) {
        filter.recipientEmail = recipientEmail.toLowerCase();
      }

      // If not admin, only show notifications for accessible emails
      if (req.user.role !== 'admin') {
        // Users can only see notifications sent to their email
        filter.recipientEmail = req.user.email;
      }

      // Pagination
      const skip = (parseInt(page) - 1) * parseInt(limit);
      const limitNum = parseInt(limit);

      // Get notifications
      const notifications = await Notification.find(filter)
        .populate('senderUserId', 'firstName lastName email role')
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limitNum);

      // Get total count
      const total = await Notification.countDocuments(filter);
      const unreadFilter = { ...filter, isRead: false };
      const unread = await Notification.countDocuments(unreadFilter);

      res.json({
        success: true,
        notifications: notifications.map(notif => ({
          id: notif._id,
          title: notif.title,
          message: notif.message,
          type: notif.type,
          priority: notif.priority,
          recipientEmail: notif.recipientEmail,
          isRead: notif.isRead,
          readAt: notif.readAt,
          emailSent: notif.emailSent,
          emailSentAt: notif.emailSentAt,
          sender: notif.senderUserId ? {
            name: `${notif.senderUserId.firstName} ${notif.senderUserId.lastName}`,
            email: notif.senderUserId.email,
            role: notif.senderUserId.role
          } : null,
          createdAt: notif.createdAt
        })),
        pagination: {
          current: parseInt(page),
          limit: limitNum,
          total,
          pages: Math.ceil(total / limitNum)
        },
        summary: {
          total,
          unread,
          filtered: notifications.length
        }
      });

    } catch (error) {
      console.error('Get notifications error:', error);
      res.status(500).json({
        success: false,
        message: 'Server error while fetching notifications'
      });
    }
  },

  // Mark notification as read
  async markRead(req, res) {
    try {
      const { id } = req.params;

      // Find notification
      const notification = await Notification.findById(id);
      
      if (!notification) {
        return res.status(404).json({
          success: false,
          message: 'Notification not found'
        });
      }

      // Check permissions (users can only mark their own notifications)
      if (req.user.role !== 'admin' && notification.recipientEmail !== req.user.email) {
        return res.status(403).json({
          success: false,
          message: 'You can only mark your own notifications as read'
        });
      }

      // Update notification
      notification.isRead = true;
      notification.readAt = new Date();
      await notification.save();

      res.json({
        success: true,
        message: 'Notification marked as read',
        notification: {
          id: notification._id,
          isRead: notification.isRead,
          readAt: notification.readAt
        }
      });

    } catch (error) {
      console.error('Mark read error:', error);
      res.status(500).json({
        success: false,
        message: 'Server error while marking notification as read'
      });
    }
  },

  // Delete notification
  async deleteNotification(req, res) {
    try {
      const { id } = req.params;

      // Find notification
      const notification = await Notification.findById(id);
      
      if (!notification) {
        return res.status(404).json({
          success: false,
          message: 'Notification not found'
        });
      }

      // Check permissions
      if (req.user.role !== 'admin' && notification.recipientEmail !== req.user.email) {
        return res.status(403).json({
          success: false,
          message: 'You can only delete your own notifications'
        });
      }

      // Delete notification
      await Notification.findByIdAndDelete(id);

      res.json({
        success: true,
        message: 'Notification deleted successfully'
      });

    } catch (error) {
      console.error('Delete notification error:', error);
      res.status(500).json({
        success: false,
        message: 'Server error while deleting notification'
      });
    }
  }
};

module.exports = notificationController;
