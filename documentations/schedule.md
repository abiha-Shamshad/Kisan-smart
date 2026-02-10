# Maintenance Schedule

## Daily
- [ ] **Check Uptime**: Verify via UptimeRobot/Pingdom.
- [ ] **Monitor Errors**: Review Sentry for new critical issues.
- [ ] **Backups**: Confirm last night's DB backup was successful (check file size).

## Weekly
- [ ] **Log Review**: Scan Nginx/App logs for suspicious activity.
- [ ] **Disk Usage**: Check server disk space (`df -h`).
- [ ] **User Feedback**: Review support tickets for recurring themes.

## Monthly
- [ ] **Updates**: Apply OS security patches (`apt update && apt upgrade`).
- [ ] **Dependencies**: Update Python/JS libraries if critical security fixes exist.
- [ ] **Performance**: Analyze slow queries in PostgreSQL (`pg_stat_statements`).
- [ ] **Cleanup**: Delete temporary files and old logs (>30 days).

## Quarterly
- [ ] **Security Audit**: Rotate secrets/passwords. Review firewall rules.
- [ ] **Disaster Recovery**: Test restoring a backup to a staging env.
- [ ] **Feature Review**: Plan next sprint/roadmap based on analytics.
