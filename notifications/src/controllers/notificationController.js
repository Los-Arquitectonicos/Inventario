const User = require('../models/User');

exports.createNotification = async (req, res) => {
  const { message, targetRole, targetUsername } = req.body;

  try {
    if (targetRole) {
      // Broadcast to role
      await User.updateMany(
        { role: targetRole },
        { $push: { notifications: { message } } }
      );
      return res.json({ msg: `Notification sent to role ${targetRole}` });
    } else if (targetUsername) {
      // Send to specific user
      const user = await User.findOne({ username: targetUsername });
      if (!user) return res.status(404).json({ msg: 'User not found' });

      user.notifications.push({ message });
      await user.save();
      return res.json({ msg: `Notification sent to user ${targetUsername}` });
    } else {
      return res.status(400).json({ msg: 'Please provide targetRole or targetUsername' });
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
