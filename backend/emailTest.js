require("dotenv").config();
const nodemailer = require("nodemailer");

async function sendTestEmail() {
  try {
    console.log("🔐 Email user:", process.env.EMAIL_USER);
    console.log(
      "🔐 Email pass exists:",
      !!process.env.EMAIL_PASS
    );

    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
      },
    });

    const info = await transporter.sendMail({
      from: `"Contract Platform" <${process.env.EMAIL_USER}>`,
      to: process.env.EMAIL_USER, // send to yourself for test
      subject: "✅ Test Email Working",
      html: `
        <h2>Email test successful 🚀</h2>
        <p>If you see this, Gmail SMTP is working.</p>
      `,
    });

    console.log("✅ Email sent:", info.messageId);
  } catch (err) {
    console.error("❌ Email failed:", err);
  }
}

sendTestEmail();
