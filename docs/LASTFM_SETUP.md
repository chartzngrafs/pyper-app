# Last.fm API Setup Guide for Pyper

Pyper's Dynamic Themed Playlists feature can optionally integrate with Last.fm to enhance theme discovery with community-driven music metadata, tags, and popularity data.

## 🎯 What Last.fm Integration Provides

- **Community Tags**: Genre, mood, and style classifications from the Last.fm community
- **Popularity Metrics**: Global vs. local popularity for "hidden gems" detection
- **Enhanced Theme Naming**: More intelligent theme names using community-driven classifications
- **Mood Analysis**: Energy levels and atmospheric descriptors from listener feedback

## 🔑 Getting Your Last.fm API Key

### Step 1: Create a Last.fm Account
1. Visit [Last.fm](https://www.last.fm) and create an account if you don't have one
2. You don't need to actively scrobble to use the API - the account is just for API access

### Step 2: Register for API Access
1. Go to [Last.fm API Registration](https://www.last.fm/api/account/create)
2. Fill out the application form:
   - **Application Name**: `Pyper Music Player` (or your preferred name)
   - **Application Description**: `Personal music player for dynamic playlist generation`
   - **Application Homepage**: Leave blank or use your personal website
   - **Application Type**: Select `Desktop Application`
3. Click "Submit" to create your API application

### Step 3: Get Your API Key
1. After registration, you'll be taken to your API account page
2. Your **API Key** will be displayed - copy this value
3. You can always find your API key later at [Last.fm API Account](https://www.last.fm/api/account)

## ⚙️ Configuring Pyper

### Method 1: Through Pyper's Advanced Settings (Recommended)
1. Launch Pyper and go to **Your Library Themes** tab
2. Click **Advanced Settings** button
3. Navigate to the **Services** tab
4. In the Last.fm section:
   - Paste your API key in the **API Key** field
   - Optionally enter your Last.fm username
   - Click **Save Settings**

### Method 2: Environment Variable
You can also set your API key as an environment variable:

```bash
export LASTFM_API_KEY="your_api_key_here"
```

Add this to your `~/.bashrc` or `~/.profile` to make it permanent.

### Method 3: Configuration File
Add the Last.fm configuration to your `config/config.json`:

```json
{
    "navidrome": {
        // ... your existing navidrome config
    },
    "ui": {
        // ... your existing ui config  
    },
    "dynamic_themes": {
        "external_apis": {
            "lastfm": {
                "api_key": "your_api_key_here",
                "username": "your_lastfm_username"
            }
        }
    }
}
```

## 🧪 Testing Your Setup

1. Go to **Your Library Themes** tab in Pyper
2. Click **Clear Cache & Re-analyze** to force fresh analysis
3. Watch the progress - you should see Last.fm API calls in the status updates
4. Check the logs (`pyper.log`) for Last.fm API activity:
   ```
   DynamicThemes.MetadataEnricher - INFO - Using Last.fm API key from configuration
   DynamicThemes.MetadataEnricher - INFO - Enhanced metadata enricher initialized with MusicBrainz + Last.fm
   ```

## 🔧 Troubleshooting

### "No Last.fm API key configured"
- Verify your API key is correctly entered in Advanced Settings
- Check that you've saved the settings after entering the key
- Restart Pyper after configuring the API key

### "Last.fm API rate limit exceeded"
- The system automatically handles rate limiting (5 calls/second)
- If you see this error, wait a few minutes and try again
- Large libraries may take longer due to rate limiting

### "Last.fm API request failed"
- Check your internet connection
- Verify your API key is valid by testing it at [Last.fm API Explorer](https://www.last.fm/api)
- Check the logs for detailed error messages

### Theme names still generic despite Last.fm setup
- Last.fm integration is part of Phase 2 Step 2 which needs refinement
- The current implementation may not fully utilize Last.fm data yet
- See `docs/AI_PLAYLIST_FEATURE.md` for current status and planned improvements

## 📊 API Usage and Limits

- **Rate Limit**: 5 calls per second (automatically handled)
- **Daily Limit**: No official daily limit for non-commercial use
- **Data Usage**: ~1-2 API calls per track during analysis
- **Caching**: Results are cached to minimize repeated API calls

## 🔒 Privacy and Data

- Pyper only uses Last.fm's **public API** for metadata lookup
- No personal listening data is sent to Last.fm
- Your API key is stored locally in Pyper's configuration
- No scrobbling or account modification is performed

## 🆘 Need Help?

- Check the [Last.fm API Documentation](https://www.last.fm/api/intro)
- Review Pyper's logs in `pyper.log` for detailed error messages
- Visit the [Last.fm API Forum](https://www.last.fm/group/Last.fm+Web+Services) for API-specific issues
- Create an issue in Pyper's repository for integration problems

---

**Note**: Last.fm integration is optional. Pyper's Dynamic Themed Playlists will work without it, using MusicBrainz data and basic metadata analysis. Last.fm enhances the experience with additional community-driven insights.

