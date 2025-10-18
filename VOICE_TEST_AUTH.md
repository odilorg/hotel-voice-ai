# Voice Agent Test Page - Authentication

## Access Details

**URL:** https://jahongir-app.uz/voice-test-secure.html

**Authentication Type:** HTTP Basic Authentication

**Credentials:**
- Username: 
- Password: 

## How to Access

### In Browser
1. Navigate to https://jahongir-app.uz/voice-test-secure.html
2. Browser will prompt for username and password
3. Enter credentials above
4. Click OK/Login
5. Test page will load

### Via curl (for testing)
```bash
# Test without credentials (should return 401)
curl -I https://jahongir-app.uz/voice-test-secure.html

# Test with credentials (should return 200)
curl -u admin:VoiceTest2025! https://jahongir-app.uz/voice-test-secure.html
```

## Implementation Details

### Nginx Configuration
Location: `/etc/nginx/sites-available/jahongir-app.uz`

```nginx
# Voice Agent Test Page - HTTP Basic Auth Protected
location = /voice-test-secure.html {
    auth_basic "Voice Agent Test - Restricted Access";
    auth_basic_user_file /var/www/jahongirnewapp/public/.htpasswd_voice;
}
```

### Password File
Location: `/var/www/jahongirnewapp/public/.htpasswd_voice`
Format: Apache htpasswd format (bcrypt encrypted)

### Backup
Original config backed up to: `/etc/nginx/sites-available/jahongir-app.uz.backup`

## Security Status

✅ HTTP Basic Authentication enabled
✅ Password file secured with bcrypt encryption
✅ Only one test page accessible (with auth)
✅ 9 other test pages moved to storage
⏳ API routes still need authentication (see SECURITY_REPORT.md)

## Changing Password

To change the password:

```bash
# SSH into server
ssh -p 2222 root@62.72.22.205

# Update password
htpasswd -cb /var/www/jahongirnewapp/public/.htpasswd_voice admin NEW_PASSWORD

# No need to reload Nginx - changes take effect immediately
```

## Adding Additional Users

```bash
# Add a new user (don't use -c flag, it overwrites the file)
htpasswd -b /var/www/jahongirnewapp/public/.htpasswd_voice newuser PASSWORD123

# Reload Nginx
systemctl reload nginx
```

## Testing

Test authentication is working:
```bash
# Should return 401 Unauthorized
curl -I https://jahongir-app.uz/voice-test-secure.html

# Should return 200 OK
curl -I -u admin:VoiceTest2025! https://jahongir-app.uz/voice-test-secure.html
```

## Notes

- HTTP Basic Auth sends credentials with every request
- Credentials are base64 encoded but NOT encrypted (HTTPS required!)
- HTTPS is already enabled, so credentials are encrypted in transit
- For production use, consider implementing Laravel authentication or API tokens
- This is suitable for internal testing and development use

---

**Implementation Date:** 2025-10-18
**Status:** Active
**Implemented By:** Claude Code
