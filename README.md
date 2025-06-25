# Pyper - A Modern Navidrome Music Player

A feature-rich, Linux-first music player application designed specifically for Navidrome servers. Built with PyQt6 and featuring a clean, modern interface with robust search capabilities, contextual information display, and comprehensive theming system.

## ✨ Features

- **🐧 Linux-First Design**: Optimized for Linux desktop environments with comprehensive system tray integration
- **🔍 Powerful Search**: Search across artists, albums, and songs with dedicated search tab
- **🎯 Enhanced Tabbed Interface**: Browse, Search, Queue, Most Played, Recently Played, Recently Added, and Radio tabs
- **📻 Advanced Internet Radio**: Stream radio stations with real-time ICY metadata, multi-source album art, and intelligent track parsing
- **🎨 Contextual Information Panel**: Dynamic bottom panel showing artist info, album details, and artwork based on your selection
- **🎵 Multi-Category Navigation**: Browse by Artists, Albums, Playlists, Genres, and Years (decades)
- **🖼️ Visual Album Grid**: Artists display albums in a beautiful responsive 3-column grid with artwork, metadata, and interactive controls
- **📊 Play Count Integration**: Display play counts from Navidrome database with remote SSH access support
- **🎨 Album Art Support**: Automatic album artwork display with proper scaling, centering, and contextual thumbnails
- **📋 Queue Management**: Full playback queue with individual track management and Clear Queue functionality
- **🎵 Scrobbling**: Last.fm compatible scrobbling through Navidrome
- **🌈 Comprehensive Theming System**: 8 custom themes plus qt-material themes with automatic text contrast
- **🖱️ Context Menus**: Right-click options throughout the interface with "Go to..." navigation
- **⚡ Smart Playbook & Album Queueing**: Double-click songs to auto-queue remainder of album from that track onward
- **🚀 Auto-Expand**: Artists automatically expanded on startup for immediate browsing
- **📝 Comprehensive Logging**: File and console logging for debugging and monitoring
- **🔗 Remote Database Access**: SSH-based access to remote Navidrome databases for play count data
- **🎯 Improved Album Layout**: Side-by-side artwork and info display with equal heights for better visual balance
- **⏯️ Time Scrubbing**: Click progress bar to seek to any position in tracks
- **🆕 Recently Added Albums**: Dedicated tab showing newest albums with creation dates
- **🧭 Smart Navigation**: "Go to..." context menu options to jump between tabs and find items in Browse section
- **🎨 Synthwave Icon**: Beautiful neon electric blue soundwave icon matching the synthwave aesthetic
- **🖥️ System Tray Integration**: Full-featured system tray with contextual menu, hover controls, and rich tooltips
- **📱 Mini Player Mode**: Compact 350x120px player with complete controls and theme integration
- **🎯 Dynamic Themed Playlists**: AI-powered library analysis discovering personalized themes through clustering algorithms

## 🎨 Theming System

Pyper includes a comprehensive theming system with **8 custom themes** plus qt-material themes:

### Custom Themes
1. **Dark Teal** (Default) - Professional dark teal with electric accents
2. **Cobalt Blue** - Deep cobalt blue with electric blue highlights
3. **IBM Patina Yellow** - Warm patina yellow inspired by IBM vintage computing
4. **Hacker Green** - Matrix-inspired green terminal theme
5. **Dracula** - Dark theme with purple accents inspired by the popular Dracula color scheme
6. **Tokyo Midnight** - Dark blue theme with neon accents inspired by Tokyo's nightlife
7. **Monochrome** - Clean black, white, and gray professional theme
8. **Synthwave '84** - Authentic 80s synthwave theme with neon electric blue highlights and hot pink accents

### Theme Features
- **Automatic Text Contrast**: Intelligent contrast calculation ensures readable text on all backgrounds
- **Real-time Switching**: Change themes instantly via View → Themes menu
- **Persistent Preferences**: Theme selection is saved and restored on startup
- **Comprehensive Coverage**: All UI elements styled consistently across themes
- **Accessibility**: Proper contrast ratios for better readability

Access themes via **View → Themes** in the menu bar.

## 🎯 Dynamic Themed Playlists

Pyper includes an **AI-powered theme discovery system** that analyzes your entire music library to automatically discover and generate personalized playlist themes based on the unique patterns and characteristics found in your collection.

### How It Works
- **Library Analysis**: Click "🔍 Discover My Themes" to analyze your music collection
- **Multi-Dimensional Clustering**: Uses K-means clustering on genre, year, play count, and duration data
- **Personalized Themes**: Discovers 10-15 unique themes specific to your library rather than generic categories
- **Smart Caching**: Analysis results are cached for instant access on subsequent visits
- **Background Processing**: Non-blocking analysis with real-time progress updates

### Theme Discovery Features
- **Intelligent Naming**: Generated theme names like "2010s Indie Rock Wave" or "Hidden Gems Alternative"
- **Theme Cards**: Visual grid display with track counts and descriptions
- **One-Click Actions**: Play, queue, or save themes directly to Navidrome playlists
- **Database Integration**: Utilizes local Navidrome database for comprehensive analysis when available
- **Performance Optimized**: Analysis completes in <30 seconds for 5000+ track libraries

### Example Discovered Themes
Based on your library's unique characteristics, you might discover themes like:
- **"2010s Indie Rock Wave"** - Your indie rock collection from the golden era of 2008-2012
- **"90s Ambient Electronic Chill"** - Perfect downtempo electronic for late night coding
- **"Hidden Gems Alternative Rock"** - Lesser-played but highly-rated tracks from your collection
- **"Folk Acoustic Journey"** - Acoustic tracks spanning multiple decades and artists

### Accessing Your Library Themes
1. Navigate to the **"Your Library Themes"** tab (between "Recently Played" and "Radio")
2. Click **"🔍 Discover My Themes"** to start analysis
3. Watch the progress as your library is analyzed in the background
4. Browse discovered themes in the responsive grid layout
5. Click **▶** to play, **+** to queue, or **💾** to save themes as playlists

The feature is designed to reveal the hidden patterns in your music collection, creating playlists that reflect your unique listening preferences and library composition.

## 📋 Requirements

- Python 3.8+
- PyQt6
- Navidrome server (configured and running)
- Linux desktop environment (tested on Manjaro/Arch)
- SSH access to Navidrome server (optional, for play count features)

## 🚀 Installation

### For Manjaro/Arch Linux:

1. **Install system dependencies:**
   ```bash
   sudo pacman -S python-pyqt6 python-requests python-pipx
   ```

2. **Install Python packages:**
    ```bash
   pip install --break-system-packages py-sonic qt-material scikit-learn numpy
    ```

3. **Clone/download Pyper and set up:**
    ```bash
   git clone <repository-url>
   cd pyper-app
   ```

4. **Configure your server settings:**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config/config.json with your Navidrome server details
   ```

5. **Run Pyper:**
    ```bash
   ./run-pyper.sh
   # or
    python pyper.py
    ```

### Alternative Installation (any Linux):

1. **Install requirements:**
   ```bash
   pip install --break-system-packages -r requirements.txt
   # Note: requirements.txt includes scikit-learn and numpy for theme discovery
   ```

2. **Configure and run as above**

## ⚙️ Configuration

Create your configuration file:

```bash
cp config/config.example.json config/config.json
```

Edit `config/config.json`:

```json
{
    "navidrome": {
        "server_url": "http://your-server:4533",
        "username": "your_username", 
        "password": "your_password",
        "database_path": "/home/user/.navidrome/navidrome.db",
        "ssh_host": "your-server-ip",
        "ssh_user": "username",
        "ssh_key_path": "~/.ssh/id_ed25519"
    },
    "ui": {
        "theme": "dark_teal.xml",
        "window_width": 1400,
        "window_height": 900
    }
}
```

**Important**: 
- Include `http://` or `https://` in your server URL
- The configuration file is ignored by git for security
- Never commit your actual credentials
- SSH configuration is optional but enables advanced play count features
- Set up SSH key authentication for seamless database access

**Common Database Locations:**
- `/var/lib/navidrome/navidrome.db` (systemd service)
- `/opt/navidrome/navidrome.db` (manual installation)  
- `/home/navidrome/navidrome.db` (user installation)

**Radio Station Configuration:**
- Configure internet radio stations through your Navidrome web interface
- Go to Settings → Internet Radio in Navidrome to add stations
- Stations will automatically appear in Pyper's Radio tab after refresh

## 🎵 Usage

### Navigation Structure
- **Browse Tab**: Navigate Artists → Albums → Songs hierarchy (auto-expands artists on startup)
  - **Artists**: Browse by artist with beautiful visual album grid - responsive 3-column layout with artwork, year, and play counts
  - **Albums**: Browse all albums with play count integration
  - **Playlists**: Access your Navidrome playlists
  - **Genres**: Browse music by genre with album previews
  - **Years**: Browse by decades (1960s, 1970s, etc.) with album counts
- **Search Tab**: Find content across your entire library
- **Queue Tab**: Manage your playback queue with individual track removal
- **Most Played Tab**: Discover your most frequently played albums with play counts
- **Recently Played Tab**: Quick access to recently played albums
- **Recently Added Tab**: Browse newest albums with creation dates
- **Radio Tab**: Stream internet radio stations configured on your Navidrome server
- **Your Library Themes Tab**: Discover personalized playlist themes through AI analysis of your music collection

### Contextual Information Panel
The bottom panel dynamically displays relevant information based on your selection:
- **Artist Selection**: Shows artist name, album count, and scrollable album artwork thumbnails
- **Album Selection**: Displays large album artwork, title, artist, year, and track count
- **Genre Selection**: Shows genre information with representative album thumbnails
- **Decade Selection**: Displays decade info with albums from that era
- **Automatic Updates**: Panel content changes as you navigate through the interface

### Search Functionality
1. Type in the search bar at the top
2. Press Enter or click "Search"
3. Results appear in Artists | Albums | Songs columns
4. Double-click or right-click any result to play or queue

### Playback Controls
- **Double-click** any song to auto-queue remainder of album from that track onward
- **Right-click** for context menu options:
  - "Add to Queue" - adds without playing
  - "Play Now" - adds to queue and starts playing immediately
  - "Go to Album/Artist/Song" - navigate to item in Browse tab
- **Player Bar**: Compact controls with artwork, progress, and time
- **Time Scrubbing**: Click anywhere on progress bar to seek to that position
- **Smart Navigation**: "Go to..." context menu options available in all tabs except Browse

### System Tray Integration
- **System Tray Icon**: Application runs in system tray with dynamic tooltips showing current track
- **Tray Click Actions**:
  - **Single Click**: Show dynamic hover popup with controls and track info
  - **Double Click**: Toggle main window visibility
  - **Middle Click**: Play/pause toggle (Linux standard)
- **Tray Context Menu**: Right-click for full menu with:
  - Complete playback controls (Play/Pause, Previous, Next, Stop)
  - Queue status display ("Queue: X tracks (Playing #Y)")
  - Theme switching submenu with all 8 themes
  - Window management (Show/Hide Main Window, Show Mini Player)
- **Rich Tooltips**: Multi-line tooltips showing track title (♪), artist (🎤), and album (💿)
- **Hover Popup Player**: 280x100px popup with album artwork, track info, and playback controls

### Mini Player Mode
- **Compact Interface**: 350x120px resizable window perfect for multitasking
- **Complete Controls**: Previous, play/pause, stop, next buttons with theme integration
- **Interactive Progress Bar**: Click-to-scrub functionality in compact format
- **Album Artwork**: 80x80px artwork display with current track information
- **Expand Button**: One-click return to full player interface
- **Theme Consistency**: Automatically matches current application theme colors

### Queue Management
- **Queue Tab**: Full queue view with clear button
- **Right-click** queue items for "Remove from Queue" or "Play Now"
- **Clear Queue** button in Queue tab to empty entire queue

### Radio Streaming
- **Radio Tab**: Access internet radio stations configured on your Navidrome server
- **Direct Streaming**: Double-click any radio station to start streaming immediately
- **Advanced ICY Metadata Parsing**: 
  - Real-time track information extraction from radio streams
  - Supports various metadata formats ("Artist - Title", "Title only", etc.)
  - Automatic parsing of stream titles with intelligent artist/track separation
  - Live updates every 10 seconds for current playing track information
- **Multi-Source Album Artwork**: 
  - **MusicBrainz + Cover Art Archive**: Primary source with comprehensive music database
  - **iTunes Search API**: Secondary fallback for mainstream music
  - **Smart Redirect Handling**: Follows HTTP 307 redirects for Cover Art Archive
  - **Intelligent Search**: Multiple query strategies for better artwork matching
  - **Fallback Graphics**: Default radio artwork when no album art is found
- **Enhanced Radio Interface**:
  - **Station Information**: View stream URL, homepage, and station details
  - **Homepage Integration**: Right-click to open station websites directly
  - **Live Track Display**: Real-time updates in player and contextual panel
  - **Visual Feedback**: Radio icon (📻) indicates radio mode vs music library
- **Contextual Radio Panel**: 
  - Dynamic updates showing current station and track information
  - Artist, title, and raw stream metadata display
  - Station details including homepage and stream URL
  - Seamless switching between radio and music library contexts
- **Smart Metadata Processing**:
  - Handles various radio stream title formats automatically
  - Cleans up track information for better API searches
  - Preserves original stream metadata for debugging
  - Robust error handling for unreliable stream metadata

### Dynamic Theme Discovery
1. **Access the Feature**: Navigate to the "Your Library Themes" tab
2. **Start Analysis**: Click "🔍 Discover My Themes" to begin library analysis
3. **Monitor Progress**: Real-time progress updates show analysis status
4. **Browse Themes**: Discovered themes appear as interactive cards in a responsive grid
5. **Theme Actions**: Each theme card offers:
   - **▶ Play**: Start playing the theme immediately
   - **+ Queue**: Add theme tracks to the current queue
   - **💾 Save**: Save theme as a Navidrome playlist
6. **Instant Access**: Once analyzed, themes are cached for immediate future access
7. **Re-analysis**: Click "Discover My Themes" again to refresh with library changes

### Album Artwork
- **Click artwork** in player to show detailed track info dialog
- **Centered Display**: Artwork is properly centered in all contexts
- **Side-by-Side Layout**: Album info shows artwork and details side-by-side with equal heights
- **Contextual thumbnails**: Small album art previews in bottom panel
- **Proper Scaling**: Maintains aspect ratio while fitting containers perfectly

### Logging
- Application events logged to `pyper.log` in the application directory
- Console output for real-time monitoring
- Error tracking and debugging information
- Startup and connection status logging

## 🏗️ Project Structure

```
pyper-app/
├── src/
│   └── pyper/
│       ├── __init__.py           # Package initialization  
│       ├── main.py               # Main application (2,325 lines)
│       ├── theme_manager.py      # Theme management system (298 lines)
│       ├── database_helper.py    # Database operations with SSH (251 lines)
│       ├── subsonic_client.py    # Navidrome API client (198 lines)
│       ├── background_tasks.py   # Threading and async operations (465 lines)
│       ├── ui_components.py      # UI widgets and dialogs (745 lines)
│       └── dynamic_themes/       # Dynamic themed playlists system
│           ├── __init__.py       # Package initialization
│           ├── dynamic_theme_engine.py  # Core theme discovery engine (440 lines)
│           └── ui/               # UI components
│               ├── __init__.py   # UI package initialization
│               ├── themed_playlists_tab.py  # Main tab UI (341 lines)
│               └── theme_discovery_thread.py  # Background processing (63 lines)
├── config/
│   ├── config.example.json      # Example configuration
│   └── config.json             # Your configuration (ignored by git)
├── themes/
│   ├── dark_teal.json          # Dark teal theme (default)
│   ├── cobalt_blue.json        # Cobalt blue theme
│   ├── synthwave84.json        # Synthwave '84 theme
│   ├── dracula.json            # Dracula theme
│   ├── tokyo_midnight.json     # Tokyo midnight theme
│   ├── hacker_green.json       # Matrix-inspired green theme
│   ├── ibm_patina_yellow.json  # IBM vintage yellow theme
│   ├── monochrome.json         # Black/white/gray theme
│   └── README.md               # Theme system documentation
├── docs/
│   ├── DATABASE_SETUP.md       # Database configuration guide
│   └── FEATURES.md             # Detailed feature documentation
├── assets/
│   ├── pyper.desktop           # Desktop entry file
│   ├── pyper-icon.png          # Application icon (128x128)
│   ├── pyper-icon-64.png       # Medium icon (64x64)
│   ├── pyper-icon-48.png       # Standard icon (48x48)
│   ├── pyper-icon-32.png       # Small icon (32x32)
│   ├── pyper-icon-16.png       # Tiny icon (16x16)
│   ├── pyper-icon.ico          # Windows ICO format
│   └── create_icon.py          # Synthwave icon generation script
├── logs/                       # Application logs directory
├── pyper.py                    # Entry point script
├── requirements.txt            # Python dependencies
├── run-pyper.sh               # Launch script with config check
├── install-shortcut.sh        # Desktop shortcut installer
├── setup.py                   # Package setup
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## 🛠️ Troubleshooting

### Configuration Issues
```bash
# Check if config exists
ls -la config/config.json

# Validate JSON syntax
python -m json.tool config/config.json

# Check log file for errors
tail -f pyper.log
```

### Connection Issues
- Verify Navidrome server is running and accessible
- Test by accessing Navidrome web interface first  
- Check URL format includes `http://` or `https://`
- Verify username and password are correct
- Check `pyper.log` for detailed connection error messages

### SSH/Database Issues
- Ensure SSH key authentication is set up correctly
- Test SSH connection manually: `ssh -i ~/.ssh/id_ed25519 user@server`
- Verify database path on remote server
- Check SSH configuration in config.json
- Application will fall back to API-based play data if SSH fails

### Audio Issues
- Ensure system has proper audio codecs installed
- Check that other audio applications work
- Verify Qt multimedia framework is installed
- Check log file for FFmpeg/audio-related errors

### Dependencies
```bash
# System packages (Manjaro/Arch)
sudo pacman -S python-pyqt6 python-requests

# Python packages
pip install py-sonic qt-material
```

## 🔧 Development

### Technology Stack
- **PyQt6**: Modern Qt bindings for Python
- **py-sonic**: Subsonic/Navidrome API client  
- **qt-material**: Material Design theme for Qt
- **SQLite3**: Database access for play count data
- **SSH/SCP**: Remote database access capabilities
- **scikit-learn**: Machine learning algorithms for theme clustering
- **NumPy**: Numerical computing for feature analysis

### Modular Architecture

Pyper follows a clean, modular architecture with separation of concerns:

#### Core Modules
- **`main.py`** (2,325 lines): Main application window, UI layout, event handling, and application logic
- **`theme_manager.py`** (298 lines): Complete theme management system with custom and qt-material theme support
- **`database_helper.py`** (251 lines): Database operations with SSH remote access for play count data
- **`subsonic_client.py`** (198 lines): Enhanced Navidrome/Subsonic API client with comprehensive endpoint support
- **`background_tasks.py`** (465 lines): Threaded operations for non-blocking UI performance
- **`ui_components.py`** (745 lines): Reusable UI widgets and specialized dialog components

#### Key Components
- **`ThemeManager`**: Handles theme loading, application, and real-time switching with automatic contrast calculation
- **`NavidromeDBHelper`**: SSH-based remote database access with connection management and play count queries  
- **`CustomSubsonicClient`**: Full-featured API client with authentication, error handling, and extended endpoints
- **`LibraryRefreshThread`**: Asynchronous library data loading for responsive startup and navigation
- **`ImageDownloadThread`**: Concurrent album artwork downloading with proper thread lifecycle management
- **`ICYMetadataParser`**: Advanced internet radio metadata parsing with multi-source album artwork fetching
- **`ContextualInfoPanel`**: Dynamic bottom panel with selection-based information display
- **`AlbumGridWidget`**: Responsive album grid with artwork, metadata, and interactive controls
- **`NowPlayingDialog`**: Detailed track information flyout with enhanced artwork display

#### Architecture Benefits
- **Separation of Concerns**: Each module handles a specific responsibility
- **Maintainability**: Clean interfaces between components make updates easier
- **Thread Safety**: Proper thread management prevents UI freezing and crashes
- **Testability**: Modular design enables focused unit testing
- **Reusability**: Components can be reused across different parts of the application
- **Performance**: Background operations don't block the main UI thread

### Logging System
- Comprehensive logging throughout the application
- File logging to `pyper.log` with rotation
- Console output for development
- Error tracking and debugging information

## 📚 Documentation

- **[Database Setup Guide](docs/DATABASE_SETUP.md)**: Detailed database configuration
- **[Features Documentation](docs/FEATURES.md)**: Complete feature overview
- **[Installation Guide](install-shortcut.sh)**: Desktop integration setup

## 🎯 Recent Updates

### v2.7 - Dynamic Themed Playlists (Phase 2 Step 2)
- **🎯 Advanced AI-Powered Theme Discovery**: Enhanced library analysis with external API integration:
  - **Multi-Dimensional Clustering**: K-means analysis enhanced with audio features, genre tags, and community metadata
  - **External API Integration**: MusicBrainz and Last.fm integration for community-driven genre and mood classification
  - **Smart Sampling Strategy**: Intelligent 6.7% sampling for large libraries achieving 20x performance improvement
  - **Advanced Audio Analysis**: Librosa integration for BPM, energy, and spectral feature extraction (configurable)
  - **Enhanced Configuration**: Comprehensive settings in Advanced Settings dialog with API key management
  - **Performance Optimization**: Analysis time reduced from 60+ minutes to 2-3 minutes for large libraries
- **🎨 Your Library Themes Tab**: Mature interface with advanced discovery capabilities:
  - **Clear Cache & Re-analyze**: Force fresh analysis bypassing all cached results
  - **Enhanced Progress Tracking**: Detailed per-track analysis progress with API call monitoring
  - **Intelligent Theme Naming**: Community-driven naming using MusicBrainz genre tags and Last.fm mood data
  - **Theme Quality Filtering**: Automatic filtering of low-coherence themes for better results
  - **Database Integration**: Full utilization of Navidrome database plus external metadata enrichment
- **⚡ Performance & Intelligence Balance**: 2-3 minute analysis for 3000+ track libraries with rich metadata integration

**Current Status**: Phase 2 Step 2 functional but needs refinement in theme naming and API data utilization. See `docs/AI_PLAYLIST_FEATURE.md` for detailed next steps.

### v2.6 - MPRIS2 Desktop Integration
- **🖥️ Full MPRIS2 Protocol Support**: Complete Linux desktop environment integration:
  - **System Media Keys**: Full support for keyboard media keys (Play/Pause, Next, Previous, Stop)
  - **Desktop Environment Integration**: Works seamlessly with GNOME, KDE, XFCE, and other desktop environments
  - **Lock Screen Controls**: Playback controls and track information available on lock screens
  - **Third-Party Application Support**: Full compatibility with playerctl, desktop widgets, and media center applications
  - **Real-Time Metadata Broadcasting**: Track title, artist, album, artwork, and duration information
  - **Threaded D-Bus Service**: Non-blocking implementation that doesn't interfere with Qt UI performance
- **🎮 Media Control Integration**: Native support for:
  - Desktop media control widgets and panels
  - Automation tools and scripting through D-Bus interface
  - Media center remote control applications
  - System notification area integration

### v2.5 - System Tray Integration & Mini Player Mode
- **🖥️ Comprehensive System Tray Integration**: Full-featured system tray icon with native Linux desktop integration:
  - **Dynamic Tooltips**: Rich multi-line tooltips showing current track with visual symbols (♪ 🎤 💿)
  - **Tray Contextual Menu**: Complete playback controls, queue status, theme switching, and window management
  - **Interactive Click Actions**: Single click for hover popup, double click to toggle window, middle click for play/pause
  - **Real-Time Updates**: All tray elements update automatically with track changes and queue modifications
- **📱 Mini Player Mode**: Compact 350x120px player window designed for multitasking:
  - **Complete Playback Controls**: Previous, play/pause, stop, next with full functionality
  - **Interactive Progress Bar**: Click-to-scrub functionality in compact format
  - **Album Artwork Display**: 80x80px artwork with current track information
  - **Theme Integration**: Automatically matches current application theme colors
  - **Expand Button**: One-click return to full player interface
- **⚡ Smart Album Queueing**: Double-click any song to automatically queue remainder of album from that track onward
- **🎯 Dynamic Hover Player**: Click tray icon for instant 280x100px popup with:
  - Album artwork (64x64px) and track information
  - Playback controls with theme-consistent styling
  - Auto-hide functionality (3 seconds idle, 1 second after mouse leaves)
  - Smart positioning with Wayland compatibility and screen bounds checking
- **🔧 Enhanced Desktop Integration**: Proper window management, theme consistency, and cross-desktop environment support

### v2.4 - Modular Architecture & Code Quality Improvements
- **🏗️ Complete Code Modularization**: Refactored monolithic 4,216-line main.py into clean, focused modules:
  - Extracted `ThemeManager` class to `theme_manager.py` (298 lines)
  - Extracted `NavidromeDBHelper` class to `database_helper.py` (251 lines) 
  - Extracted `CustomSubsonicClient` class to `subsonic_client.py` (198 lines)
  - Extracted threading classes to `background_tasks.py` (465 lines)
  - Extracted UI components to `ui_components.py` (745 lines)
  - **45% code reduction**: main.py reduced from 4,216 → 2,325 lines
- **🧵 Enhanced Thread Safety**: Fixed critical thread management issues preventing app crashes:
  - Added proper thread cleanup in `AlbumGridWidget` with `active_threads` tracking
  - Implemented `cleanup_threads()` method for safe thread termination
  - Enhanced application close event to prevent orphaned threads
  - Fixed "QThread: Destroyed while thread is still running" crashes
- **🔧 Improved Maintainability**: Clean separation of concerns with focused responsibilities:
  - Each module handles a single aspect (themes, database, API, UI, threading)
  - Simple import system with no complex dependencies
  - Self-contained classes with clear interfaces
  - Better error handling and logging throughout
- **⚡ Performance Optimizations**: Background operations no longer block main UI thread
- **🧪 Enhanced Testability**: Modular design enables focused unit testing of individual components
- **📚 Updated Documentation**: Comprehensive architecture documentation with module responsibilities

### v2.3 - Enhanced Navigation, Time Scrubbing & Synthwave Icon
- Added **⏯️ Time Scrubbing**: Click progress bar to seek to any position in tracks
- Implemented **🆕 Recently Added Albums Tab**: Browse newest albums with creation dates positioned between Queue and Most Played tabs
- Created **🧭 Smart Navigation System**: "Go to..." context menu options in all non-Browse tabs:
  - "Go to Album" - navigate to album in Browse > Albums
  - "Go to Artist" - navigate to artist in Browse > Artists  
  - "Go to Song" - navigate to album and select specific song
  - Available in Queue, Search Results, Most Played, Recently Played, and Recently Added tabs
- Designed **🎨 New Synthwave Icon**: Beautiful neon electric blue soundwave in circle design
  - Multiple icon sizes (16px to 128px) for all contexts
  - Windows ICO format support for cross-platform compatibility
  - Matches synthwave theme aesthetic perfectly
- Updated **🎨 Synthwave '84 Theme Colors**: Swapped hot pink for electric blue highlights with pink "Now Playing" text
- Enhanced **📱 Desktop Integration**: Updated desktop shortcut and application menu entries with new icon
- Improved **🎯 Contextual Panel Layout**: Increased height and better text wrapping to eliminate cutoff issues

### v2.2 - Advanced Radio with Multi-Source Album Art & ICY Metadata
- Added **📻 Internet Radio Tab** with full streaming capabilities and advanced metadata support
- Implemented **comprehensive ICY (Icecast) metadata parsing** for real-time track information:
  - Automatic parsing of various stream title formats ("Artist - Title", "Title only", etc.)
  - Live updates every 10 seconds with intelligent artist/track separation
  - Raw metadata preservation for debugging and comprehensive track info
- **Multi-source album artwork system** with robust fallback mechanisms:
  - **MusicBrainz + Cover Art Archive** as primary source with redirect handling
  - **iTunes Search API** as secondary fallback for mainstream music
  - **Smart query strategies** with multiple search approaches per source
  - **Automatic title cleanup** removing parenthetical info for better API matching
  - **Default radio artwork** generation when no album art is found
- **Enhanced radio interface and user experience**:
  - **Dynamic contextual panel** with real-time station and track information
  - **Visual radio indicators** (📻) distinguishing radio from music library playback
  - **Homepage integration** allowing direct access to radio station websites
  - **Comprehensive error handling** with detailed logging for troubleshooting
- **Seamless integration** with existing music library features:
  - Smooth switching between radio and music library playback
  - Consistent UI behavior across radio and music modes
  - Full integration with theming system and contextual information display

### v2.1 - Comprehensive Theming & UI Polish
- Added **comprehensive theming system** with 8 custom themes
- Implemented **automatic text contrast calculation** for all themes
- Created **side-by-side album layout** with equal height artwork and info sections
- Fixed **album artwork centering** issues across all display contexts
- Added **real-time theme switching** with persistent preferences
- Included **authentic Synthwave '84 theme** with proper neon colors
- Enhanced **accessibility** with proper contrast ratios in all themes
- Improved **visual consistency** across all UI elements

### v2.0 - Enhanced Navigation & Contextual Interface
- Added **Genres** and **Years** navigation categories
- Implemented **dynamic contextual information panel**
- Added **comprehensive logging system**
- Enhanced **remote database access** with SSH support
- Improved **album artwork handling** with thumbnails
- Added **decade-based year browsing**
- Enhanced **error handling and debugging**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the repository for license details.

## 🙏 Acknowledgments

- **Navidrome**: The excellent music server that powers this player
- **PyQt6**: For the robust GUI framework
- **qt-material**: For the beautiful material design theme