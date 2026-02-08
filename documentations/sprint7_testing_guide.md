# Sprint 7 Frontend Testing Guide

## Quick Verification Checklist

### Registration Page (`/register`)
- [ ] Page loads with Bootstrap 5 styling
- [ ] Password strength indicator updates as you type
- [ ] All 5 password requirements show green checkmarks when met
- [ ] Username validation shows error for invalid format
- [ ] Email validation shows error for invalid format
- [ ] Password mismatch shows error
- [ ] Form submits via AJAX (check Network tab)
- [ ] Success toast appears on successful registration
- [ ] Button shows loading spinner during submission
- [ ] Mobile responsive (hamburger menu visible < 768px)

### Login Page (`/login`)
- [ ] Email and password fields validate properly
- [ ] Show/hide password toggle works
- [ ] Remember me checkbox present
- [ ] Form submits via AJAX
- [ ] JWT token stored in localStorage (check Application tab)
- [ ] Success toast and redirect to dashboard
- [ ] Error messages display for invalid credentials
- [ ] "Forgot Password" and "Sign Up" links work

### Forgot Password (`/forgot-password`)
- [ ] Email field validates
- [ ] Form submits via AJAX
- [ ] Success message shows after submission
- [ ] Page updates to confirm email sent

### Reset Password (`/reset-password/<token>`)
- [ ] Token extracted from URL
- [ ] Password strength indicator works
- [ ] Confirmation password validates
- [ ] Success redirects to login
- [ ] Invalid/expired token shows error

### Email Verification (`/verify-email/<token>`)
- [ ] Shows loading spinner initially
- [ ] Auto-verifies on page load
- [ ] Success shows checkmark and countdown
- [ ] Auto-redirects after 5 seconds
- [ ] Invalid token shows error
- [ ] Manual "Continue to Login" button works

### Navigation
- [ ] Logo clickable (goes to home)
- [ ] Nav links work
- [ ] Auth links visible when logged out
- [ ] User menu visible when logged in
- [ ] Logout function clears token
- [ ] Mobile hamburger menu works

### Browser Console Tests
```javascript
// Test API client
await api.isAuthenticated()  // Should return true/false
api.getToken()  // Should return token or null

// Test validators
Validators.validateEmail('test@example.com')  // Should return {valid: true}
Validators.validateUsername('abc')  // Should return {valid: true}
Validators.calculatePasswordStrength('Passw0rd!')  // Should return 2 (strong)

// Test auth manager
auth.getCurrentUser()  // Should return user object if logged in
```

## Common Issues & Solutions

### Issue: API calls fail
- **Check**: Is Flask server running on port 5000?
- **Check**: CORS enabled in Sprint 6 API?
- **Solution**: Verify API endpoints in browser console Network tab

### Issue: JWT token not stored
- **Check**: localStorage in DevTools > Application
- **Solution**: Ensure API returns `access_token` in response

### Issue: Forms don't submit
- **Check**: Browser console for JavaScript errors
- **Solution**: Verify all JS files loaded (check Network tab)

### Issue: Styles not applied
- **Check**: Static files serving correctly
- **Solution**: Clear browser cache, check static file URLs

### Issue: Password strength not updating
- **Check**: Console for errors in validators.js
- **Solution**: Verify all requirement IDs match HTML

## Next Steps
After verifying Sprint 7, you can proceed to:
- Sprint 8: Core Application UI (Prediction Input & Results)
- Implement dashboard with prediction form
- Display fertilizer recommendations
- Show prediction history
