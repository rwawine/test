# 🎉 Telegram Lottery Bot - Installation Guide

## 📋 Overview

This is a comprehensive Telegram bot system for conducting fair lottery drawings with participant registration, admin panel, and support system. The system uses DuckDB for data storage and includes a Flask-based web admin interface.

## 🏗️ Architecture

### Core Components
- **Telegram Bot**: User registration and interaction via aiogram
- **Web Admin Panel**: Flask-based management interface
- **Database**: DuckDB for lightweight, embedded storage
- **Lottery System**: Cryptographically secure random selection
- **Support System**: Ticket-based user support
- **Broadcast System**: Mass messaging capabilities

### Key Features
- ✅ Multi-step registration with validation
- ✅ Photo upload for leaflet verification
- ✅ Fair lottery algorithm with public verification
- ✅ Comprehensive admin panel
- ✅ Support ticket system
- ✅ Mass messaging/broadcast system
- ✅ Export functionality (Excel, CSV, PDF)
- ✅ Real-time statistics and monitoring

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Admin Telegram IDs

### Step 1: Clone and Setup Environment

```bash
# Clone the repository (or extract files)
cd /path/to/lottery_bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

1. Copy the `.env` file and update with your values:

```bash
# Update .env file with your settings
BOT_TOKEN=your_actual_bot_token_here
ADMIN_IDS=123456789,987654321
SECRET_KEY=your-super-secret-key-for-web-admin
```

2. Key configuration parameters:

```env
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Admin Telegram IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# Database file path
DATABASE_PATH=lottery_bot.duckdb

# Web admin panel settings
SECRET_KEY=change-this-secret-key
WEB_PORT=5000
WEB_HOST=127.0.0.1

# File storage paths
UPLOAD_FOLDER=uploads
EXPORT_FOLDER=exports
LOG_FOLDER=logs

# Lottery configuration
MAX_PARTICIPANTS=10000
```

### Step 3: Initialize Database

The database will be automatically created when you first run the bot. You can also test the setup:

```bash
python test_system.py
```

This will verify:
- All imports work correctly
- Database initialization
- Validation functions
- Lottery system basics

### Step 4: Run the System

```bash
python main.py
```

This will start both:
- Telegram bot (listening for messages)
- Web admin panel (http://localhost:5000)

## 🌐 Web Admin Panel

### Access
- URL: `http://localhost:5000`
- Default login: `admin` / `admin123`
- **⚠️ Change the password in production!**

### Features
- Dashboard with statistics
- Participant management
- Lottery system
- Broadcast management
- Support ticket system
- Data export

## 🤖 Bot Commands and Features

### User Commands
- `/start` - Start interaction with bot
- **Main Menu Buttons:**
  - 🚀 Начать регистрацию
  - 📋 Мой статус  
  - ❓ Помощь
  - 💬 Техподдержка
  - 📊 О розыгрыше

### Admin Commands
- `/admin` - Admin mode access
- `/stats` - Quick statistics
- `/export` - Quick data export

## 📊 Registration Process

### User Flow
1. **Name Input**: Full name validation
2. **Phone Number**: Russian format (+7XXXXXXXXXX)
3. **Loyalty Card**: 8-16 digit validation
4. **Photo Upload**: Leaflet photo with file validation
5. **Confirmation**: Review and submit
6. **Admin Review**: Pending → Approved/Rejected

### Validation Rules
- **Name**: 2-50 characters, letters only
- **Phone**: Russian format, unique per user
- **Loyalty Card**: 8-16 digits, unique per user
- **Photo**: JPG/PNG/GIF, max 10MB

## 🎲 Lottery System

### Fair Algorithm
- Cryptographically secure random seed generation
- Deterministic selection based on SHA-256
- Public hash for verification
- Reproducible results

### Process
1. Generate secure random seed
2. Create public hash for verification
3. Select winners deterministically
4. Store results with proof-of-fairness
5. Notify winners via Telegram

### Verification
Anyone can verify results by:
1. Checking SHA-256(seed) = published_hash
2. Running the same algorithm with the seed
3. Comparing results

## 📨 Support System

### Features
- FAQ with common questions
- Ticket creation with categories
- File attachment support
- Admin response system
- Ticket status tracking

### Categories
- Photo problems
- Loyalty card issues
- Technical problems
- Application status
- Lottery questions
- Other issues

## 📡 Broadcast System

### Capabilities
- Mass messaging to all users
- Targeted messaging by status
- Template-based messages
- Image support
- Delivery tracking
- Failed delivery handling

### Target Audiences
- All participants
- Approved only
- Pending applications
- Winners only
- Custom selections

## 🔧 Maintenance

### Logs
- Bot logs: `logs/bot.log`
- Web app logs: Console output
- Error tracking: Built-in logging

### Database Backup
```bash
# DuckDB files are single files, easy to backup
cp lottery_bot.duckdb lottery_bot_backup_$(date +%Y%m%d).duckdb
```

### File Cleanup
```bash
# Clean old uploads (optional)
python -c "from utils.file_handler import clean_old_files; clean_old_files('uploads', 30)"
```

## 🔒 Security Considerations

### Production Deployment
1. **Change default passwords**
2. **Use HTTPS for web admin**
3. **Restrict admin panel access by IP**
4. **Regular database backups**
5. **Monitor file uploads**
6. **Rate limiting for bot**

### Recommended Setup
```bash
# Use environment variables
export BOT_TOKEN="your_token"
export ADMIN_IDS="id1,id2"

# Run with process manager
pip install gunicorn supervisor

# Use reverse proxy (nginx)
# Configure SSL certificates
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check Python path and virtual environment
   python test_system.py
   ```

2. **Database Issues**
   ```bash
   # Delete and recreate database
   rm lottery_bot.duckdb
   python main.py
   ```

3. **Bot Not Responding**
   - Check BOT_TOKEN in .env
   - Verify bot is started with /start in Telegram
   - Check logs for errors

4. **Web Admin Access**
   - Default: admin/admin123
   - Check web server is running on correct port
   - Verify firewall settings

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## 📞 Support

For technical issues:
1. Check logs first (`logs/bot.log`)
2. Run system tests (`python test_system.py`)
3. Verify configuration (`.env` file)
4. Check database connectivity

## 🚀 Production Deployment

### Recommended Stack
- **Server**: Linux VPS/Cloud instance
- **Process Manager**: Supervisor or systemd
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt certificates
- **Monitoring**: System logs + health checks

### Deployment Steps
1. Setup server environment
2. Configure reverse proxy
3. Setup SSL certificates
4. Configure process manager
5. Setup automated backups
6. Monitor system health

---

## 📈 System Statistics

The system tracks:
- Total participants
- Registration trends
- Approval rates
- Support ticket volume
- Broadcast delivery rates
- System uptime and errors

All statistics are available in the web admin dashboard with real-time updates.

## 🎯 Next Steps

After installation:
1. Test registration flow
2. Configure admin accounts
3. Setup monitoring
4. Plan lottery schedule
5. Prepare announcement materials
6. Train support staff

**Good luck with your lottery system! 🍀**