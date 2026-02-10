#!/bin/bash
# Automated backup script for Kisan Smart database (PostgreSQL)

set -e

# Configuration
BACKUP_DIR="/home/kisansmart/backups/database"
DB_NAME="kisan_smart"
DB_USER="kisansmart"
DB_HOST="localhost"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create directory
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting PostgreSQL backup for $DB_NAME at $DATE..."
PGPASSWORD="YOUR_DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.dump"

echo "Backup created: $BACKUP_DIR/db_backup_$DATE.dump"

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "db_backup_*.dump" -mtime +$RETENTION_DAYS -delete

echo "Backup process completed successfully."
echo ""
echo "To restore this backup, use:"
echo "  pg_restore -h localhost -U $DB_USER -d $DB_NAME $BACKUP_DIR/db_backup_$DATE.dump"
