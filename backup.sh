#!/bin/bash
#
# Backup script for Telegram Lottery Bot
# Run daily via cron: 0 2 * * * /opt/lottery-bot/backup.sh
#

set -e

# Configuration
APP_DIR="/opt/lottery-bot"
BACKUP_DIR="/opt/lottery-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lottery_backup_${DATE}"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Starting backup at $(date)"

# Create temporary backup directory
TEMP_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "${TEMP_DIR}"

# Backup database
if [ -f "${APP_DIR}/lottery_bot.duckdb" ]; then
    cp "${APP_DIR}/lottery_bot.duckdb" "${TEMP_DIR}/"
    echo "✓ Database backed up"
fi

# Backup uploads
if [ -d "${APP_DIR}/uploads" ]; then
    cp -r "${APP_DIR}/uploads" "${TEMP_DIR}/"
    echo "✓ Uploads backed up"
fi

# Backup configuration (without secrets)
cp "${APP_DIR}/config.py" "${TEMP_DIR}/" 2>/dev/null || true
cp "${APP_DIR}/requirements.txt" "${TEMP_DIR}/" 2>/dev/null || true

# Create tarball
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

echo "✓ Backup created: ${BACKUP_NAME}.tar.gz"

# Calculate size
SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
echo "✓ Backup size: ${SIZE}"

# Clean old backups
find "${BACKUP_DIR}" -name "lottery_backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "✓ Old backups cleaned (older than ${RETENTION_DAYS} days)"

echo "Backup completed at $(date)"

# Optional: Upload to remote storage
# aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" s3://your-backup-bucket/
# rclone copy "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" remote:backup/