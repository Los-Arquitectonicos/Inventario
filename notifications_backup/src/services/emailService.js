const nodemailer = require('nodemailer');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: process.env.SMTP_PORT || 587,
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASSWORD
      }
    });
  }

  async sendNotificationEmail(notification) {
    const { recipientEmail, title, message, type, priority } = notification;

    const typeIcons = {
      info: '📢',
      warning: '⚠️',
      error: '❌',
      success: '✅'
    };

    const priorityColors = {
      low: '#6B7280',
      medium: '#F59E0B',
      high: '#EF4444'
    };

    const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ProvesiWMS Notification</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 30px 40px 20px; text-align: center; background-color: #1F2937; border-radius: 8px 8px 0 0;">
                                <h1 style="margin: 0; color: white; font-size: 24px;">ProvesiWMS Notifications</h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <div style="border-left: 4px solid ${priorityColors[priority]}; padding-left: 20px; margin-bottom: 20px;">
                                    <h2 style="margin: 0 0 10px 0; color: #1F2937; display: flex; align-items: center;">
                                        <span style="margin-right: 10px; font-size: 24px;">${typeIcons[type]}</span>
                                        ${title}
                                    </h2>
                                    <p style="margin: 0; color: #6B7280; text-transform: uppercase; font-size: 12px; font-weight: bold;">
                                        ${type} • ${priority} priority
                                    </p>
                                </div>
                                
                                <div style="background-color: #F9FAFB; padding: 20px; border-radius: 6px; margin: 20px 0;">
                                    <p style="margin: 0; color: #374151; line-height: 1.6; font-size: 16px;">
                                        ${message}
                                    </p>
                                </div>
                                
                                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                                    <p style="margin: 0; color: #6B7280; font-size: 14px;">
                                        Sent: ${new Date().toLocaleString()}<br>
                                        Recipient: ${recipientEmail}
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 20px 40px; background-color: #F9FAFB; border-radius: 0 0 8px 8px; text-align: center;">
                                <p style="margin: 0; color: #6B7280; font-size: 12px;">
                                    This is an automated notification from ProvesiWMS.<br>
                                    Please do not reply to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    `;

    const mailOptions = {
      from: `"ProvesiWMS Notifications" <${process.env.EMAIL_FROM || process.env.EMAIL_USER}>`,
      to: recipientEmail,
      subject: `${typeIcons[type]} ${title} - ProvesiWMS`,
      html: htmlContent,
      text: `${title}\n\n${message}\n\nType: ${type}\nPriority: ${priority}\nSent: ${new Date().toLocaleString()}`
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      console.log(`📧 Email sent to ${recipientEmail}: ${info.messageId}`);
      return {
        success: true,
        messageId: info.messageId,
        sentAt: new Date()
      };
    } catch (error) {
      console.error(`❌ Email failed to ${recipientEmail}:`, error.message);
      return {
        success: false,
        error: error.message,
        sentAt: new Date()
      };
    }
  }

  async testConnection() {
    try {
      await this.transporter.verify();
      console.log('✅ Email service connection verified');
      return true;
    } catch (error) {
      console.error('❌ Email service connection failed:', error.message);
      return false;
    }
  }
}

module.exports = new EmailService();