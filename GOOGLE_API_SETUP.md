# Google API Setup Guide

## Required Google APIs

To use Google OAuth authentication, you need to enable the following APIs in Google Cloud Console:

### 1. Google+ API (or Google Identity API)

**Note:** Google+ API was deprecated, but the userinfo endpoint is now part of the Google Identity Platform.

### 2. Enable Required APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Library**
4. Search for and enable:
   - **Google+ API** (if still available) OR
   - **Google Identity Services API** (newer)

Actually, for OAuth 2.0 with OpenID Connect, you typically don't need to enable additional APIs - the OAuth 2.0 endpoints are available by default.

## OAuth Consent Screen Setup

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have a Google Workspace account)
3. Fill in the required information:
   - App name: "Secret Santa"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users (if app is in Testing mode):
   - Add your Google account email
6. Save and continue

## OAuth 2.0 Client ID Setup

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Choose **Web application**
4. Configure:
   - **Name**: Secret Santa App
   - **Authorized JavaScript origins**: 
     - `http://localhost:8000` (for development)
     - `https://your-domain.com` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/google/callback`
     - `https://your-domain.com/auth/google/callback`
5. Click **CREATE**
6. Copy the **Client ID** and **Client Secret** to your `.env` file

## Common Issues

### Issue: "Access blocked: This app's request is invalid"

**Solution:**
- Make sure your OAuth consent screen is properly configured
- If your app is in "Testing" mode, add your email as a test user
- Wait a few minutes after making changes

### Issue: "Error 400: redirect_uri_mismatch"

**Solution:**
- Double-check that the redirect URI in Google Console exactly matches what your app is using
- Make sure you're using `http://` for localhost and `https://` for production
- Include the port number if using a non-standard port

### Issue: "Authentication failed" after successful Google login

**Possible causes:**
1. **Missing userinfo endpoint access**: The app needs to fetch user info from Google's API
2. **Incorrect scopes**: Make sure `openid email profile` scopes are requested
3. **Token exchange failure**: Check that your Client ID and Secret are correct

**Solution:**
- Verify your `.env` file has the correct `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Check the application logs for detailed error messages
- Make sure the OAuth consent screen has the required scopes approved

## Testing

1. Make sure your `.env` file is configured:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

2. Start your application:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

3. Navigate to `http://localhost:8000/login`
4. Click "Sign in with Google"
5. You should be redirected to Google's login page
6. After logging in, you should be redirected back to your app

## Debugging

If authentication fails, check:
1. Application logs for error messages
2. Browser console for any errors
3. Google Cloud Console → APIs & Services → Credentials → Check OAuth client configuration
4. Verify the redirect URI matches exactly

The application now includes better error logging - check your terminal output for detailed error messages.

