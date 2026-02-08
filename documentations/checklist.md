# Launch Checklist

## Technical Readiness
- [ ] **Tests**: All unit and integration tests passing (`pytest`).
- [ ] **Security**: 
    - [ ] `SECRET_KEY` changed in production.
    - [ ] Debug mode disabled (`FLASK_DEBUG=0`).
    - [ ] SSL certificate installed and valid.
- [ ] **Database**:
    - [ ] Migrations applied (`flask db upgrade`).
    - [ ] Initial seed data loaded (if applicable).
    - [ ] Backup system verified.
- [ ] **Performance**:
    - [ ] Static assets compressed/minified.
    - [ ] Nginx caching configured.

## Content & Support
- [ ] **Documentation**: User manual and admin guide published.
- [ ] **Legal**: Privacy Policy and Terms of Services accessibile.
- [ ] **Support**: Help email (`support@kisansmart.com`) active.

## Marketing
- [ ] Social media announcement ready.
- [ ] Emails drafted for beta users.
- [ ] Landing page visuals updated.

## Post-Launch
- [ ] Monitor error logs (Sentry).
- [ ] Check server load (CPU/RAM).
- [ ] Verify backup generation after 24h.
