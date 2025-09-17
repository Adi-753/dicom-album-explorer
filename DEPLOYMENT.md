# DICOM Album Explorer - Deployment Guide

This guide covers how to deploy your DICOM Album Explorer application to various cloud platforms.

## 🚀 What's New

Your application has been significantly enhanced for production deployment:

### ✅ Features Added:
- **User Authentication**: Registration, login, and session management
- **Database Support**: PostgreSQL for production, SQLite for development
- **Shareable Albums**: Generate public links to share albums
- **Cloud Storage**: AWS S3 integration for scalable file storage
- **Production Configuration**: Environment-based settings
- **Error Handling**: Comprehensive error handling and logging
- **Docker Support**: Containerized deployment
- **Security**: Password hashing, CSRF protection, input validation

## 🏗️ Architecture

### Development (Local)
- SQLite database
- Local file storage
- Flask development server

### Production (Cloud)
- PostgreSQL database
- AWS S3 file storage
- Gunicorn WSGI server
- Docker containerization

## 📋 Prerequisites

1. **Python 3.11+**
2. **Docker** (for containerized deployment)
3. **AWS Account** (for S3 storage in production)
4. **PostgreSQL database** (for production)

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Flask Configuration
FLASK_ENV=production  # or development
SECRET_KEY=your-super-secret-key-here-minimum-32-chars
DEBUG=false

# Database (for production)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Authentication
ENABLE_USER_AUTH=true
ENABLE_SHARING=true

# AWS S3 (for production file storage)
USE_CLOUD_STORAGE=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1
```

## 🐳 Docker Deployment

### Local Development with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Access the application
# App: http://localhost:5000
# Database: localhost:5432
# PgAdmin: http://localhost:8080
```

### Production Docker Deployment

```bash
# Build the image
docker build -t dicom-explorer .

# Run the container
docker run -p 5000:5000 \
  -e DATABASE_URL=your_postgres_url \
  -e SECRET_KEY=your_secret_key \
  -e AWS_S3_BUCKET=your_bucket \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  dicom-explorer
```

## ☁️ Cloud Platform Deployment

### 1. Railway (Recommended - Easiest)

1. **Create Railway Account**: https://railway.app
2. **Connect GitHub**: Link your repository
3. **Add PostgreSQL**: Add PostgreSQL service to your project
4. **Set Environment Variables**:
   ```
   SECRET_KEY=your-secret-key
   ENABLE_USER_AUTH=true
   ENABLE_SHARING=true
   USE_CLOUD_STORAGE=true
   AWS_S3_BUCKET=your-bucket
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   ```
5. **Deploy**: Railway will automatically deploy using `railway.toml`

### 2. Heroku

1. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set ENABLE_USER_AUTH=true
   heroku config:set ENABLE_SHARING=true
   heroku config:set USE_CLOUD_STORAGE=true
   heroku config:set AWS_S3_BUCKET=your-bucket
   heroku config:set AWS_ACCESS_KEY_ID=your-key
   heroku config:set AWS_SECRET_ACCESS_KEY=your-secret
   ```

4. **Create Procfile**:
   ```
   web: gunicorn app:app
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

### 3. DigitalOcean App Platform

1. **Create App**: Connect your GitHub repository
2. **Configure Build**: 
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
3. **Add Database**: Create PostgreSQL database
4. **Set Environment Variables**: Same as Railway/Heroku
5. **Deploy**: Automatic deployment on git push

## 🗄️ Database Setup

### PostgreSQL Production Setup

1. **Create Database**:
   ```sql
   CREATE DATABASE dicom_albums;
   CREATE USER dicom_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE dicom_albums TO dicom_user;
   ```

2. **Connection String**:
   ```
   postgresql://dicom_user:your_password@localhost:5432/dicom_albums
   ```

### Automatic Migration

The application automatically creates necessary tables on first run.

## 📦 AWS S3 Setup

### 1. Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-dicom-bucket --region us-east-1
```

### 2. Configure Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT:user/your-user"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-dicom-bucket/*"
    }
  ]
}
```

### 3. Create IAM User

1. Create user with programmatic access
2. Attach policy with S3 permissions
3. Save Access Key ID and Secret Access Key

## 🚦 Testing Deployment

### Health Check
Visit `/health` endpoint to verify deployment:
```json
{"status": "healthy", "app": "DICOM Album Explorer"}
```

### User Registration
1. Visit `/register` to create an account
2. Login at `/login`
3. Upload DICOM files and create albums
4. Test sharing functionality

## 📊 Monitoring & Logging

### Application Logs
- Production logs are stored in `logs/dicom_explorer.log`
- Logs rotate automatically (10MB max, 10 backups)

### Database Monitoring
- Monitor PostgreSQL performance
- Set up alerts for connection issues

### Storage Monitoring
- Monitor S3 usage and costs
- Set up CloudWatch alarms

## 🔒 Security Considerations

### Production Security Checklist:
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS/SSL in production
- [ ] Use environment variables for secrets
- [ ] Regular database backups
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated
- [ ] Use WAF if possible

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Errors**:
   - Check DATABASE_URL format
   - Verify database credentials
   - Ensure database is running

2. **S3 Upload Failures**:
   - Verify AWS credentials
   - Check bucket permissions
   - Confirm bucket exists

3. **Authentication Issues**:
   - Clear browser cookies
   - Check SECRET_KEY consistency
   - Verify database user table

### Debug Mode:
Never enable debug mode in production. For troubleshooting, check logs instead.

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Confirm S3 permissions

## 🔄 Updates

To update your deployment:
1. Push changes to your repository
2. Platform will automatically redeploy
3. Database schema updates are automatic
4. Monitor logs for any issues

---

Your DICOM Album Explorer is now ready for production deployment! 🎉