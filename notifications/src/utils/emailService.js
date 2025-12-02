const nodemailer = require('nodemailer');

const sendEmail = async (to, subject, text) => {
  // Create a transporter
  // Note: In production, use environment variables for these values
  // For now, we'll try to use a generic SMTP or just log if not configured
  
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: process.env.SMTP_PORT || 587,
    secure: false, // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER, // generated ethereal user
      pass: process.env.SMTP_PASS, // generated ethereal password
    },
  });

  // Provisionally override the recipient
  const provisionalRecipient = 'pedropablost@icloud.com';

  const mailOptions = {
    from: process.env.SMTP_FROM || '"ProvesiWMS Notifications" <no-reply@provesi.com>',
    to: provisionalRecipient, // Overridden as requested
    subject: subject,
    text: text,
  };

  try {
    if (!process.env.SMTP_USER || !process.env.SMTP_PASS) {
        console.log('⚠️ SMTP credentials not found. Skipping email send.');
        console.log(`[MOCK EMAIL] To: ${provisionalRecipient}, Subject: ${subject}, Body: ${text}`);
        return;
    }

    const info = await transporter.sendMail(mailOptions);
    console.log('Message sent: %s', info.messageId);
  } catch (error) {
    console.error('Error sending email:', error);
  }
};

module.exports = sendEmail;
