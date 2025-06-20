# Pyper Features Documentation

This document provides a comprehensive overview of all features available in Pyper, the modern Navidrome music player.

## 🎵 Core Music Player Features

### Audio Playback
- **High-Quality Streaming**: Direct streaming from Navidrome server with FFmpeg support
- **Multiple Format Support**: FLAC, MP3, OGG, and other formats supported by Navidrome
- **Gapless Playback**: Smooth transitions between tracks
- **ReplayGain Support**: Automatic volume normalization when available in metadata
- **Scrobbling**: Last.fm compatible scrobbling through Navidrome integration

### Player Controls
- **Standard Controls**: Play, Pause, Stop, Previous, Next
- **Progress Bar**: Visual playback progress with seek functionality (purple themed)
- **Time Display**: Current time and total duration
- **Album Artwork**: Clickable artwork that opens detailed track information
- **Now Playing Display**: Current track title and artist information

## 🗂️ Navigation & Browsing

### Multi-Category Navigation
Pyper provides five distinct browsing categories plus dedicated tabs for enhanced functionality:

#### 1. Artists
- **Hierarchical Browsing**: Artists → Albums → Songs
- **Auto-Expansion**: Artists category automatically selected and expanded on startup
- **Album Thumbnails**: Contextual panel shows album artwork thumbnails for selected artist
- **Play Count Integration**: Album listings include play counts when available

#### 2. Albums
- **Complete Album Listing**: All albums with artist information
- **Play Count Display**: Shows play counts in format "Album Name (X plays)"
- **Year Information**: Album year displayed when available
- **Direct Album Access**: Click album to view songs directly

#### 3. Playlists
- **Navidrome Playlists**: Access all your server-side playlists
- **Playlist Songs**: Direct access to playlist contents
- **Playlist Management**: View and play playlist entries

#### 4. Genres
- **Genre Discovery**: Browse music by genre categories
- **Genre Albums**: View all albums within a specific genre
- **Genre Statistics**: Album count per genre displayed
- **Contextual Preview**: Genre panel shows representative album thumbnails

#### 5. Years (Decades)
- **Decade Browsing**: Music organized by decades (1960s, 1970s, etc.)
- **Album Counts**: Number of albums per decade displayed
- **Year Range Filtering**: Automatic decade-based album filtering
- **Chronological Organization**: Decades sorted from newest to oldest

### Additional Tabs
- **Search Tab**: Global search across all content types
- **Queue Tab**: Playback queue management with track removal and clear options
- **Most Played Tab**: Albums ranked by play frequency from database
- **Recently Played Tab**: Albums ordered by last played date
- **Radio Tab**: Internet radio stations with live metadata and album artwork

### Search Functionality
- **Global Search**: Search across artists, albums, and songs simultaneously
- **Three-Column Results**: Separate results for Artists | Albums | Songs
- **Real-Time Search**: Results update as you type
- **Search Tab Integration**: Dedicated search interface
- **Context Menu Support**: Right-click options on all search results

## 🎯 Contextual Information Panel

The dynamic bottom panel provides relevant information based on your current selection:

### Artist Context
- **Artist Information**: Name and album count
- **Album Thumbnails**: Scrollable horizontal view of up to 8 album covers
- **Quick Album Access**: Visual preview of artist's discography
- **Automatic Loading**: Artwork loads asynchronously for smooth performance

### Album Context
- **Large Artwork Display**: 100x100px album cover with proper scaling
- **Detailed Metadata**: Album title, artist, year, and track count
- **Loading States**: Shows "Loading..." while fetching artwork
- **Fallback Display**: "No Art" message when artwork unavailable

### Genre Context
- **Genre Information**: Genre name and album statistics
- **Representative Albums**: Album thumbnails from the genre
- **Visual Discovery**: Preview albums before diving deeper
- **Album Count Display**: Shows total albums in genre

### Decade Context
- **Decade Information**: Decade name (e.g., "1970s") and statistics
- **Era Albums**: Album thumbnails from the selected decade
- **Historical Browsing**: Visual timeline of your music collection
- **Period Statistics**: Album count for the decade

### Radio Context
- **Station Information**: Current radio station name and details
- **Live Track Display**: Real-time artist and title from ICY metadata
- **Stream Details**: Stream URL and homepage information
- **Raw Metadata**: Original stream title for debugging purposes
- **Dynamic Updates**: Content updates automatically as tracks change

### Default State
- **Helpful Message**: Guidance text when no item is selected
- **Clean Interface**: Uncluttered appearance when not in use
- **Responsive Design**: Adapts to different content types automatically

## 📊 Play Count & Statistics

### Database Integration
- **Local Database Access**: Direct SQLite access to Navidrome database
- **Remote Database Support**: SSH-based access to remote Navidrome servers
- **Play Count Display**: Shows actual play counts from Navidrome
- **API Fallback**: Uses Navidrome API when database unavailable

### SSH Configuration
- **Secure Access**: SSH key-based authentication
- **Automatic Database Copying**: Temporary local copies for fast access
- **Connection Resilience**: Automatic fallback to API methods
- **Cleanup Management**: Automatic temporary file cleanup

### Statistics Display
- **Album Play Counts**: "Album Name (X plays)" format throughout interface
- **Most Played Tab**: Albums ranked by play frequency
- **Recently Played Tab**: Albums ordered by last play date
- **Artist Album Counts**: Play counts in artist album listings

## 🎼 Queue Management

### Queue Operations
- **Add to Queue**: Add songs without interrupting current playback
- **Play Now**: Add songs to queue and start playing immediately
- **Queue Visualization**: Dedicated Queue tab with full track listing
- **Queue Position**: Visual indication of current playing track

### Queue Controls
- **Individual Track Removal**: Right-click to remove specific tracks
- **Clear Queue**: One-click button to empty entire queue
- **Queue Reordering**: Manual track position management
- **Play from Queue**: Click any queue item to jump to that track

### Context Menu Options
Available throughout the interface:
- **"Add to Queue"**: Adds content without playing
- **"Play Now"**: Adds to queue and starts playback
- **"Remove from Queue"**: Removes specific queue items

## 📻 Internet Radio System

### Radio Station Management
- **Navidrome Integration**: Automatically loads radio stations configured in Navidrome
- **Station Discovery**: Stations appear in dedicated Radio tab after library refresh
- **Station Information**: View stream URLs, homepage links, and station details
- **Direct Streaming**: Double-click any station to start immediate playback

### Advanced ICY Metadata Parsing
- **Real-Time Track Information**: Continuous parsing of ICY metadata from radio streams
- **Multiple Format Support**: Handles various stream title formats:
  - "Artist - Title" (standard format)
  - "Title only" (when artist unknown)
  - "Artist - Title (Year)" (with additional info)
- **Live Updates**: Metadata refreshed every 10 seconds automatically
- **Intelligent Parsing**: Smart separation of artist and track information
- **Raw Metadata Preservation**: Original stream data kept for debugging

### Multi-Source Album Artwork System
- **Primary Source - MusicBrainz + Cover Art Archive**:
  - Comprehensive music database with extensive artwork collection
  - Multiple query strategies for better matching accuracy
  - Smart redirect handling (HTTP 307) for Cover Art Archive
  - Release-based artwork matching for higher quality results
- **Secondary Source - iTunes Search API**:
  - Mainstream music coverage with high-quality artwork
  - Automatic search term optimization (removes parenthetical info)
  - High-resolution artwork conversion (600x600px)
  - Fallback for tracks not found in MusicBrainz
- **Intelligent Search Processing**:
  - Multiple query formats tried per source for best results
  - Automatic title cleanup for better API matching
  - Smart timeout and retry handling for reliable operation
  - Comprehensive error handling with detailed logging
- **Default Artwork Generation**:
  - Custom radio artwork created when no album art found
  - Musical note symbol (♪) on gray background
  - Consistent 200x200px sizing for uniform display
  - Immediate fallback to maintain visual consistency

### Radio Interface Features
- **Visual Radio Indicators**: 📻 emoji clearly distinguishes radio from music playback
- **Contextual Radio Panel**: Dynamic bottom panel updates with:
  - Current station name and stream information
  - Real-time track artist and title
  - Stream URL and homepage links (when available)
  - Raw metadata display for technical users
- **Homepage Integration**: Right-click radio stations to open their websites directly
- **Seamless Mode Switching**: Smooth transitions between radio and music library playback
- **Consistent UI Behavior**: Radio playback integrates fully with existing theme system

### Radio Streaming Technology
- **Direct Stream Playback**: Bypasses queue system for continuous radio streaming
- **ICY Metadata Protocol**: Full support for Icecast metadata parsing
- **Stream Reliability**: Robust connection handling with automatic reconnection
- **Background Processing**: Metadata parsing runs in separate thread for UI responsiveness
- **Memory Management**: Efficient cleanup of metadata parsing resources

### Radio Configuration
- **Navidrome Setup**: Configure stations through Navidrome web interface
- **Settings Location**: Access via Settings → Internet Radio in Navidrome
- **Automatic Discovery**: Stations automatically appear in Pyper after refresh
- **No Additional Setup**: Zero configuration required in Pyper itself

## 🔍 Search System

### Search Capabilities
- **Multi-Category Search**: Simultaneous search across all content types
- **Real-Time Results**: Instant results as you type
- **Exact Match Support**: Finds exact artist, album, and song matches
- **Partial Matching**: Flexible search with partial string matching

### Search Interface
- **Dedicated Tab**: Full-screen search interface
- **Three-Column Layout**: Organized results display
- **Search Bar**: Top-level search input with Enter key support
- **Auto-Tab Switching**: Automatically switches to Search tab when searching

### Search Results
- **Artist Results**: Artist names with album counts
- **Album Results**: "Album - Artist" format with years
- **Song Results**: "Song - Artist" format with durations
- **Clickable Results**: Double-click or right-click for actions

## 🎨 User Interface

### Modern Design
- **Dark Theme**: qt-material dark_teal theme
- **Purple Accents**: Custom purple progress bar and highlights
- **Clean Layout**: Uncluttered, professional appearance
- **Responsive Design**: Adapts to different window sizes

### Layout Structure
- **Top Toolbar**: Search bar, refresh button, and status display
- **Player Bar**: Compact controls with artwork and progress (100-120px height)
- **Tabbed Browser**: Main content area with multiple tabs
- **Contextual Panel**: Dynamic bottom panel (120px height) with selection info

### Visual Elements
- **Album Artwork**: Properly scaled artwork throughout interface
- **Thumbnail Galleries**: Horizontal scrolling album previews
- **Loading States**: Visual feedback during data loading
- **Status Messages**: Real-time feedback on operations

## 📝 Logging & Debugging

### Logging System
- **File Logging**: Comprehensive logs written to `pyper.log`
- **Console Output**: Real-time logging to terminal
- **Log Levels**: INFO, ERROR, and DEBUG level messages
- **Timestamped Entries**: Full timestamp and component identification

### Logged Events
- **Application Startup**: Initialization and configuration loading
- **Connection Events**: Navidrome server connection status
- **Database Operations**: SSH connections and database queries
- **Error Tracking**: Detailed error messages with stack traces
- **User Actions**: Search operations and navigation events

### Debug Information
- **API Calls**: Navidrome API request and response logging
- **Database Queries**: SQL query execution and results
- **SSH Operations**: Remote database access attempts
- **Image Loading**: Artwork download and processing status

## ⚙️ Configuration Management

### Configuration File
- **JSON Format**: Human-readable configuration in `config/config.json`
- **Example Template**: `config.example.json` provides structure
- **Security**: Configuration file ignored by git for credential protection
- **Validation**: JSON syntax validation on startup

### Configuration Sections
- **Navidrome Settings**: Server URL, credentials, database path
- **SSH Configuration**: Remote access settings for database
- **UI Settings**: Theme, window size, and interface preferences
- **Database Settings**: Local and remote database configuration

### Advanced Features
- **Remote Database Access**: SSH-based database copying and access
- **Theme Customization**: qt-material theme selection
- **Window Management**: Configurable window dimensions
- **Fallback Mechanisms**: API fallback when database unavailable

## 🚀 Performance Features

### Threaded Operations
- **Library Refresh**: Background library loading
- **Image Downloads**: Asynchronous artwork loading
- **Database Access**: Non-blocking database operations
- **SSH Operations**: Background remote database copying

### Caching & Optimization
- **Artwork Caching**: Intelligent image caching for performance
- **Database Caching**: Temporary local database copies
- **Connection Pooling**: Efficient API connection management
- **Memory Management**: Proper widget cleanup and memory handling

### Responsive Interface
- **Non-Blocking UI**: All heavy operations run in background threads
- **Progress Feedback**: Visual indicators for long-running operations
- **Smooth Scrolling**: Optimized list and scroll performance
- **Fast Search**: Instant search results with minimal latency

## 🔧 Integration Features

### Navidrome Integration
- **Full API Support**: Complete Subsonic API implementation
- **Authentication**: Secure token-based authentication
- **Scrobbling**: Last.fm compatible play tracking
- **Playlist Support**: Full playlist integration

### System Integration
- **Desktop Entry**: Linux desktop integration with `.desktop` file
- **Icon Support**: Custom application icon
- **File Associations**: Potential for music file associations
- **System Tray**: Future system tray integration support

### Development Features
- **Modular Architecture**: Clean separation of concerns
- **Extensible Design**: Easy to add new features
- **Error Handling**: Comprehensive error recovery
- **Code Documentation**: Well-documented codebase

This comprehensive feature set makes Pyper a powerful, modern music player specifically designed for Navidrome users who want a rich, desktop music experience with advanced browsing capabilities and contextual information display. 