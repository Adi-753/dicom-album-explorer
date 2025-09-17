# DICOM Album Explorer - FREE Deployment Guide 🆓

This guide covers how to deploy your DICOM Album Explorer application using **completely free** cloud platforms.

## 🎯 100% Free Deployment Options

### 1. Railway (Recommended - Most Generous Free Tier)

**What you get for FREE:**
- 512MB RAM
- 1GB Disk Storage  
- PostgreSQL database included
- Custom domain support
- Automatic deploys from GitHub

**Steps:**
1. **Sign up**: Go to https://railway.app (use GitHub login)
2. **Create New Project**: Click "New Project"
3. **Deploy from GitHub**: Connect your repository
4. **Add Database**: Click "Add Service" → PostgreSQL
5. **Set Environment Variables**:
   ```
   SECRET_KEY=your-random-32-character-secret-key-here
   FLASK_ENV=production
   ENABLE_USER_AUTH=true
   ENABLE_SHARING=true
   USE_CLOUD_STORAGE=false
   ```
6. **Deploy**: Railway will automatically build and deploy!

### 2. Render (Great Free Option)

**What you get for FREE:**
- 512MB RAM
- Automatic SSL
- Custom domains
- PostgreSQL database
- GitHub integration

**Steps:**
1. **Sign up**: Go to https://render.com
2. **New Web Service**: Connect your GitHub repo
3. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Add PostgreSQL**: Create free PostgreSQL database
5. **Environment Variables**: Same as Railway above
6. **Deploy**: Automatic deployment!

### 3. Fly.io (Good for Docker Deployments)

**What you get for FREE:**
- 256MB RAM (3 apps)
- 3GB storage
- Custom domains
- Global deployment

**Steps:**
1. **Install Fly CLI**: Download from https://fly.io/docs/getting-started/installing-flyctl/
2. **Sign up**: `fly auth signup`
3. **Deploy**: `fly launch` (in your project directory)
4. **Add Database**: `fly postgres create` (free tier available)

### 4. Vercel (Serverless Option)

**Note**: Vercel is better for static sites, but can work with Python using serverless functions.

## 🗄️ Free Database Options

### 1. Railway PostgreSQL (Recommended)
- Included with Railway deployment
- No setup required

### 2. Neon (Free PostgreSQL)
- Sign up at https://neon.tech
- 3GB storage free
- Copy connection string to your app

### 3. Supabase (Free PostgreSQL + More)
- Sign up at https://supabase.com
- 500MB database free
- Includes authentication features

### 4. SQLite (Simplest for Small Usage)
- No external database needed
- Included in your app deployment
- Perfect for personal/demo use

## 📁 Free File Storage Options

Since AWS S3 costs money, here are free alternatives:

### 1. Local Storage (Recommended for Free Deployment)
**Configuration**:
```env
USE_CLOUD_STORAGE=false
```
- Files stored directly on the deployment platform
- Works great for Railway/Render free tiers
- No additional configuration needed

### 2. Cloudinary (Free Tier)
- 25GB storage free
- Image optimization included
- Good for medical images

### 3. Firebase Storage (Free Tier)
- 5GB storage free
- Google integration

## ⚙️ Free-Optimized Configuration

Update your `.env` for free deployment:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-random-key-minimum-32-characters
DEBUG=false

# Database - Railway provides this automatically
# DATABASE_URL will be set automatically by Railway/Render

# Authentication (Free features)
ENABLE_USER_AUTH=true
ENABLE_SHARING=true

# Storage (Free - use local storage)
USE_CLOUD_STORAGE=false
UPLOAD_FOLDER=./uploads
ALBUMS_FOLDER=./albums
MAX_CONTENT_LENGTH=10485760  # 10MB to stay within free limits

# App Settings
APP_NAME=DICOM Album Explorer
```

## 🚀 Step-by-Step Railway Deployment (Recommended)

### 1. Prepare Your Code
```powershell
# Make sure all files are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Deploy on Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically:
   - Detect it's a Python app
   - Install dependencies
   - Start your app

### 3. Add Database
1. In your Railway project, click "New Service"
2. Select "PostgreSQL"
3. Railway automatically connects it to your app

### 4. Set Environment Variables
1. Go to your web service
2. Click "Variables" tab
3. Add:
   ```
   SECRET_KEY = generate-random-32-char-string
   FLASK_ENV = production
   ENABLE_USER_AUTH = true
   ENABLE_SHARING = true
   USE_CLOUD_STORAGE = false
   ```

### 5. Your App is Live! 🎉
- Railway provides a URL like: `https://your-app-name.up.railway.app`
- Visit `/register` to create your first account
- Start uploading DICOM files!

## 💾 Free Tier Limitations & Solutions

### Storage Limits
**Problem**: Free tiers have limited storage
**Solution**: 
- Optimize DICOM file sizes
- Implement file cleanup for old uploads
- Use compression where possible

### Memory Limits  
**Problem**: 512MB RAM limit
**Solution**:
- Process files one at a time
- Clear memory after processing
- Use pagination for large datasets

### Bandwidth Limits
**Problem**: Limited monthly bandwidth
**Solution**:
- Compress images for web display
- Implement caching
- Optimize file serving

## 🛠️ Free Development Tools

### 1. GitHub (Code Repository)
- Unlimited public repositories
- Version control and collaboration

### 2. VS Code (IDE)
- Free, powerful code editor
- Great Python extensions

### 3. GitHub Actions (CI/CD)
- Free build/deployment automation
- Automatic testing

## 📊 Monitoring (Free Options)

### 1. Railway Built-in Monitoring
- View logs and metrics in dashboard
- No additional setup required

### 2. UptimeRobot (Free Monitoring)
- Monitor if your app is online
- Email alerts for downtime
- Free for up to 50 monitors

## 🔒 Security on Free Tier

### Essential Security (No Cost):
- ✅ Use strong SECRET_KEY
- ✅ Enable HTTPS (automatic on Railway/Render)
- ✅ Input validation (built into your app)
- ✅ Password hashing (bcrypt - included)
- ✅ Session security (Flask-Login)

## 🐛 Troubleshooting Free Deployments

### Common Issues:

1. **App Won't Start**
   - Check logs in Railway dashboard
   - Verify all environment variables are set
   - Ensure `requirements.txt` is complete

2. **Database Connection Errors**
   - Railway auto-connects PostgreSQL
   - Check if DATABASE_URL is automatically set

3. **File Upload Issues**
   - Reduce MAX_CONTENT_LENGTH if hitting memory limits
   - Check available disk space in dashboard

4. **App Sleeping (Render)**
   - Free Render apps sleep after 15 minutes
   - They wake up when accessed (may take 30 seconds)

## 🎯 Quick Start Commands

```powershell
# 1. Clone and setup
git clone your-repo
cd dicom_album_explorer
cp .env.example .env
# Edit .env with your settings

# 2. Test locally
pip install -r requirements.txt
python app.py

# 3. Deploy to Railway
# Just push to GitHub and connect on railway.app!
git add .
git commit -m "Ready for deployment"  
git push origin main
```

## 💡 Tips for Free Deployment Success

1. **Start Small**: Deploy with basic features first
2. **Monitor Usage**: Keep an eye on free tier limits
3. **Optimize**: Compress files and optimize database queries
4. **Backup**: Export data regularly (free tiers can have data limits)
5. **Document**: Keep track of your configuration

## 🎉 Your Free DICOM Explorer is Ready!

With these free options, you can:
- ✅ Deploy your app online for free
- ✅ Have users register and login
- ✅ Share DICOM albums with public links
- ✅ Store files and data at no cost
- ✅ Use a real PostgreSQL database
- ✅ Get a custom domain (optional)

**Total Monthly Cost: $0.00** 🎊

---

**Questions?** 
- Railway has great documentation and Discord community
- Render has excellent support docs
- Your app includes built-in error handling and logging