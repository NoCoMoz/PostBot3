# Voices Ignited Bot - Droplet Update Guide

This guide provides step-by-step instructions for updating the DigitalOcean droplet and the Telegram bot.

## 1. Connect to the Droplet

```bash
ssh root@64.23.176.81
```

## 2. System Updates

### 2.1. Check Available Updates
```bash
# Update package list
apt update

# See what packages can be upgraded
apt list --upgradable
```

### 2.2. Perform System Updates
```bash
# Stop the bot service first
systemctl stop voicesbot

# Upgrade all packages
apt upgrade -y

# Remove unused packages
apt autoremove -y

# Clean up package cache
apt clean

# Start the bot service
systemctl start voicesbot

# Verify service status
systemctl status voicesbot
```

## 3. Python Package Updates

### 3.1. Check Outdated Packages
```bash
# Navigate to bot directory
cd /root/voices-ignited-bot

# Activate virtual environment
source venv/bin/activate

# List outdated packages
pip list --outdated
```

### 3.2. Update Python Packages
```bash
# Stop the bot service
systemctl stop voicesbot

# Update packages using requirements.txt
pip install -r requirements.txt

# Start the bot service
systemctl start voicesbot

# Check service status
systemctl status voicesbot
```

## 4. Bot Service Management

### 4.1. Service Commands
```bash
# Start the service
systemctl start voicesbot

# Stop the service
systemctl stop voicesbot

# Restart the service
systemctl restart voicesbot

# Check service status
systemctl status voicesbot

# View service logs
journalctl -u voicesbot -n 50
```

### 4.2. Check Bot Logs
```bash
# View last 50 log entries
journalctl -u voicesbot -n 50

# Follow logs in real-time
journalctl -u voicesbot -f
```

## 5. Important Notes

1. **Current Package Versions** (as of Feb 2025):
   - python-telegram-bot==13.15
   - python-dotenv>=0.19.0
   - google-api-python-client>=2.0.0
   - google-auth-httplib2>=0.1.0
   - google-auth-oauthlib>=0.4.6
   - APScheduler==3.10.4
   - cachetools==5.3.2
   - googleapis-common-protos==1.67.0
   - urllib3==1.26.20

2. **Backup Considerations**:
   - The bot automatically backs up the Google Sheet daily at midnight UTC
   - Backups are stored in `/root/voices-ignited-bot/backups/`
   - Only the last 5 backups are kept

3. **Service Location**:
   - Bot code: `/root/voices-ignited-bot/`
   - Service file: `/etc/systemd/system/voicesbot.service`
   - Virtual environment: `/root/voices-ignited-bot/venv/`
   - Log access: `journalctl -u voicesbot`

## 6. Troubleshooting

### 6.1. If Bot Stops Working
```bash
# Check service status
systemctl status voicesbot

# View recent logs
journalctl -u voicesbot -n 50

# Restart the service
systemctl restart voicesbot

# Verify it's running
systemctl status voicesbot
```

### 6.2. If Updates Break Something
1. Check the logs for errors:
   ```bash
   journalctl -u voicesbot -n 100
   ```

2. Restore from backup if needed:
   ```bash
   cd /root/voices-ignited-bot
   source venv/bin/activate
   python restore_from_backup.py
   ```

3. Roll back package versions using the requirements.txt file

## 7. Security Best Practices

1. Always stop the bot service before updating
2. Keep regular backups of the Google Sheet
3. Monitor system resources:
   ```bash
   # Check disk space
   df -h
   
   # Check memory usage
   free -h
   
   # Check running processes
   top
   ```

## 8. Regular Maintenance Schedule

1. **Daily**:
   - Check service status
   - Verify backups are running

2. **Weekly**:
   - Update system packages
   - Check logs for errors

3. **Monthly**:
   - Clean up old backups
   - Check disk space
   - Update Python packages if needed

Remember to always test the bot's functionality after any updates by running through the quiz to ensure everything works correctly.
