#!/bin/bash
# Automated backup script for Kisan Smart database

set -e

# Configuration
BACKUP_DIR="/home/kisansmart/backups/database"
DB_NAME="kisan_smart"
DB_USER="kisansmart"
DB_PASS="YOUR_DB_PASSWORD" # Use .my.cnf in production for security
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create directory
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting backup for $DB_NAME at $DATE..."
mysqldump -u "$DB_USER" -p"$DB_PASS" --single-transaction --quick --lock-tables=false "$DB_NAME" | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

echo "Backup created: $BACKUP_DIR/db_backup_$DATE.sql.gz"

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup process completed successfully."
