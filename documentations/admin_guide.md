# Kisan Smart - Administrator Guide

## 1. System Requirements

To host Kisan Smart, the server must meet these minimum specifications:
- **OS**: Ubuntu 22.04 / 24.04 LTS
- **CPU**: 2 vCPU
- **RAM**: 4GB
- **Storage**: 40GB SSD
- **Database**: PostgreSQL 14+
- **Runtime**: Python 3.10+

---

## 2. Installation & Configuration

### Quick Install
Use the provided deployment script:
```bash
sudo ./deployment/deploy.sh
```

### Configuration (.env)
The application is configured via environment variables in `.env`:
```ini
FLASK_ENV=production
SECRET_KEY=complex_random_string
DATABASE_URL=postgresql://user:pass@localhost/kisan_smart
MAIL_USERNAME=noreply@kisansmart.com
MAIL_PASSWORD=smtp_password
```

### Nginx & SSL
Nginx acts as the reverse proxy. SSL is managed by Certbot:
```bash
sudo certbot --nginx -d kisansmart.com
```

---

## 3. Database Management

### Backups
Backups are automated via cron (`/etc/cron.d/kisan-backup`):
- **Frequency**: Daily at 02:00 AM.
- **Retention**: 30 days.
- **Location**: `/home/kisansmart/backups/database`.

**Manual Backup:**
```bash
./deployment/backup_db.sh
```

**Restoring Data:**
```bash
pg_restore -h localhost -U kisansmart -d kisan_smart backups/db_backup_20231025.dump
```

### Migrations
When code updates change the database schema:
```bash
flask db upgrade
```

---

## 4. Monitoring & Maintenance

### Logs
- **Application Logs**: `/var/log/kisansmart/app.log`
- **Error Logs**: `/var/log/nginx/kisansmart_error.log`
- **Supervisor Logs**: `/var/log/kisansmart/supervisor_err.log`

### Health Check
Monitor the endpoint `https://kisansmart.com/health` returns HTTP 200 JSON:
```json
{"status": "healthy", "components": {"db": true, "ml": true}}
```

### Updates
To update the application:
1. Pull latest code: `git pull`
2. Update deps: `pip install -r requirements.txt`
3. Migrate DB: `flask db upgrade`
4. Restart: `sudo supervisorctl restart kisansmart`

---

## 5. Security Best Practices
- **Firewall**: Ensure UFW only allows ports 22, 80, 443.
- **Secrets**: Rotate `SECRET_KEY` and database passwords every 90 days.
- **Updates**: Run `apt update && apt upgrade` monthly.
- **Monitoring**: Review Sentry for unhandled exceptions weekly.
