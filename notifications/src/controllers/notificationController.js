const User = require('../models/User');
const sendEmail = require('../utils/emailService');

exports.createNotification = async (req, res) => {
  const { message, title, type, priority, targetRole, targetUsername } = req.body;

  const notificationData = {
    message,
    title,
    type: type || 'info',
    priority: priority || 'normal',
    timestamp: new Date()
  };

  try {
    if (targetRole) {
      // Broadcast to role
      await User.updateMany(
        { role: targetRole },
        { $push: { notifications: notificationData } }
      );
      
      // Send email to all users in role (provisionally to one address)
      // In a real scenario, we might fetch emails, but here we just trigger one email or loop
      // For simplicity and the provisional requirement, we'll send one email saying "Broadcast to role"
      await sendEmail(null, `New Notification for ${targetRole}: ${title}`, message);

      return res.json({ msg: `Notification sent to role ${targetRole}` });

    } else if (targetUsername) {
      // Send to specific user
      const user = await User.findOne({ username: targetUsername });
      if (!user) return res.status(404).json({ msg: 'User not found' });

      user.notifications.push(notificationData);
      await user.save();

      await sendEmail(null, `New Notification: ${title}`, message);

      return res.json({ msg: `Notification sent to user ${targetUsername}` });

    } else {
      // Default: Send to authenticated user (Self-notification)
      // This fixes the error when no target is provided in the test script
      const user = await User.findById(req.user.id);
      if (!user) return res.status(404).json({ msg: 'User not found' });

      user.notifications.push(notificationData);
      await user.save();

      await sendEmail(null, `New Notification: ${title}`, message);

      return res.json({ msg: 'Notification sent to self', _id: user.notifications[user.notifications.length - 1]._id });
    }
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};

exports.getNotifications = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('notifications');
    res.json(user.notifications);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};

exports.markRead = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    const notification = user.notifications.id(req.params.id);

    if (!notification) {
      return res.status(404).json({ msg: 'Notification not found' });
    }

    notification.read = true;
    await user.save();

    res.json(user.notifications);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};

exports.deleteNotification = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    
    // Use pull to remove the subdocument
    user.notifications.pull(req.params.id);
    await user.save();

    res.json({ msg: 'Notification removed' });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
};
