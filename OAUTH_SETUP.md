# Google OAuth Setup Guide

## Error: redirect_uri_mismatch

This error occurs when the redirect URI used by your application doesn't match what's registered in Google Cloud Console.

## Step 1: Find Your Redirect URI

Your application uses this redirect URI pattern:
```
http://YOUR_DOMAIN/auth/google/callback
```

**For local development:**
```
http://localhost:8000/auth/google/callback
http://127.0.0.1:8000/auth/google/callback
```

**For production (if using Cloudflare Tunnel or domain):**
```
https://your-domain.com/auth/google/callback
```

**For ss.xandr2.com:**
```
https://ss.xandr2.com/auth/google/callback
```

## Step 2: Register Redirect URI in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID (or create one if you don't have it)
5. Under **Authorized redirect URIs**, click **+ ADD URI**
6. Add your redirect URI(s):

   **For local development, add:**
   ```
   http://localhost:8000/auth/google/callback
   http://127.0.0.1:8000/auth/google/callback
   ```

   **For production, add:**
   ```
   https://your-domain.com/auth/google/callback
   ```

   **For ss.xandr2.com, add:**
   ```
   https://ss.xandr2.com/auth/google/callback
   ```

7. Click **SAVE**

## Step 3: Verify Your Configuration

Make sure your `.env` file has the correct credentials:

```env
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
# Optional: Explicitly set redirect URI (if not set, app auto-detects from request)
# GOOGLE_REDIRECT_URI=https://ss.xandr2.com/auth/google/callback
```

## Step 4: Test

1. Restart your application
2. Try logging in again
3. The redirect URI should now match

## Common Issues

### Issue: Still getting redirect_uri_mismatch

**Solution:** 
- Make sure you're accessing the app from the exact URL you registered (e.g., if you registered `localhost`, don't use `127.0.0.1`)
- Check that the port number matches (e.g., `:8000`)
- Ensure you're using `http://` for localhost and `https://` for production
- Wait a few minutes after saving - Google's changes can take a moment to propagate

### Issue: Different redirect URI in production

If you're deploying to a different domain, you'll need to:
1. Add the production redirect URI to Google Cloud Console
2. Make sure your `.env` file has the correct `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

## Quick Debug: Check What Redirect URI Is Being Used

To see what redirect URI your app is generating, temporarily add this to your code or check the browser's network tab when clicking "Sign in with Google". The redirect URI will be in the Google OAuth URL.

The redirect URI format is:
```
{scheme}://{host}:{port}/auth/google/callback
```

Where:
- `scheme` = `http` (localhost) or `https` (production)
- `host` = `localhost`, `127.0.0.1`, or your domain
- `port` = `8000` (or whatever port you're using)

