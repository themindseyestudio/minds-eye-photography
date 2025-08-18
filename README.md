# Mind's Eye Photography Website

## 🚀 Railway Deployment Ready

This repository contains the complete Mind's Eye Photography website ready for deployment on Railway.

### ✅ Features Implemented
- **Contact Form**: Working email functionality with confirmations sent from rick@themindseyestudio.com
- **Portfolio Gallery**: Lightbox image viewing with category filtering
- **Mobile Responsive**: Optimized for all devices including iPhone Safari/Chrome
- **Admin Panel**: Complete portfolio management system
- **Image Upload**: Persistent storage with EXIF data extraction
- **Background Management**: Dynamic background image system

### 🔧 Railway Environment Variables Required

Set these in your Railway dashboard:

```
FLASK_APP=main.py
FLASK_ENV=production
OPENAI_API_KEY=your_openai_key
OPENAI_API_BASE=your_openai_base
```

### 📁 Project Structure
```
src/
├── main.py              # Flask application entry point
├── models/
│   └── user.py         # Database models
├── routes/
│   ├── admin.py        # Admin panel routes
│   └── api.py          # API endpoints
└── static/
    ├── index.html      # Main website
    ├── portfolio_fix.js # Frontend functionality
    └── assets/         # Image storage
```

### 🎯 Deployment Steps
1. Upload this code to your GitHub repository
2. Connect GitHub repo to Railway
3. Set environment variables in Railway dashboard
4. Railway will auto-deploy!

### 📧 Email Configuration
Contact form sends emails from rick@themindseyestudio.com to customer email addresses.
SMTP configuration is already set up in the code.

### 🎨 Admin Access
- URL: `/admin/login`
- Manage portfolio, featured images, and site content

---
**Ready for production deployment!** 🚀

