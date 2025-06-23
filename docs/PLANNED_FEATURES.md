# Pyper - Planned Features Roadmap

This document outlines upcoming features planned for Pyper, focusing on deep Linux desktop integration and enhanced music discovery capabilities.

## ✅ Recently Implemented Features

The following features have been successfully implemented and are now available in Pyper:

### Desktop Integration (Completed)
- ✅ **System Tray Integration**: Full-featured tray icon with contextual menu and hover controls
- ✅ **Mini Player Mode**: Compact 350x120px player with complete controls and theme integration
- ✅ **Smart Album Queueing**: Double-click songs to auto-queue remainder of album from that track onward
- ✅ **Tray Contextual Menu**: Complete playback controls, queue management, and theme switching
- ✅ **Dynamic Hover Player**: Click tray for instant 280x100px popup with controls and track info
- ✅ **Rich Tooltips**: Multi-line tooltips with track information and visual symbols
- ✅ **Wayland Compatibility**: Proper popup positioning and window management

## 🐧 Deep Linux Desktop Integration (Remaining)

### MPRIS2 Protocol Support
- **Full MPRIS2 D-Bus Implementation**: Complete media control protocol support for Linux desktop environments
- **Desktop Media Control**: Integration with system media keys and desktop media controls
- **Lock Screen Integration**: Playback controls and track information on KDE/GNOME lock screens
- **Metadata Broadcasting**: Real-time artist, album, track, and artwork information to desktop services

### Enhanced Desktop Experience (Remaining)
- **Global Hotkeys System**:
  - Standard media key support (Play/Pause, Next, Previous, Volume)
  - Custom keyboard shortcuts (Ctrl+Alt+P for play/pause, etc.)
  - Configurable hotkey bindings in preferences
  - Support for multimedia keyboards and gaming peripherals
- **Desktop Notifications with Album Art**:
  - Rich notifications showing track changes with album artwork
  - Theme-aware notification styling matching current Pyper theme
  - Clickable notifications for quick player access
  - Configurable notification timing and display options

## 🎵 Music Discovery Engine

### Intelligent Discovery Features
- **Smart Recommendations Panel**:
  - "Similar Artists" based on listening history and genre analysis
  - "You Might Like" albums using collaborative filtering from play patterns
  - "Rediscover" feature highlighting forgotten favorites from your library
  - Integration with Last.fm/ListenBrainz for enhanced recommendations
- **Smart Playlist Creation**:
  - Right-click any track to generate "Create Smart Playlist" based on that selection
  - Automatic playlist generation using similar tempo, genre, mood, and era
  - "More Like This" instant playlist creation from current playing track
  - Configurable playlist length and similarity parameters

### Contextual Discovery Tools
- **Mood-Based Browsing**:
  - Automatic mood classification of your library (energetic, chill, melancholic, etc.)
  - Genre-crossing mood playlists ("Chill Electronic + Ambient Rock")
  - Time-based suggestions ("Morning Energizers", "Late Night Vibes")
  - Weather-aware recommendations using system location data

## 📊 Visual Music Exploration
- **Interactive Genre Map**:
  - Network visualization of genre relationships in your library
  - Clickable genre nodes to explore related music
  - Visual representation of your musical taste clusters
  - Discovery paths between different music styles

## 🔧 Technical Implementation Notes

### Desktop Integration Architecture
- **New Module**: `desktop_integration.py` for MPRIS and system integration
- **D-Bus Integration**: Native Linux inter-process communication
- **XDG Standards Compliance**: Proper Linux desktop environment integration
- **Systemd User Service**: Optional background service for persistent tray functionality

### Music Discovery Backend
- **New Module**: `discovery_engine.py` for recommendation algorithms
- **Local Analysis**: Privacy-first approach using only local library data
- **Pluggable Backends**: Support for Last.fm, ListenBrainz, and local-only modes
- **Caching System**: Efficient storage of analysis results and recommendations

### Data Privacy Considerations
- **Local-First Approach**: All discovery features work without external services
- **Opt-In External Integration**: Users choose what data to share with external services
- **Transparent Data Usage**: Clear indication of what data is used for each feature
- **Secure Network Discovery**: Encrypted local network communication for music sharing

## 🎯 Implementation Priority

### Phase 1: Advanced Desktop Integration
1. MPRIS2 protocol implementation
2. Global hotkeys system  
3. Desktop notifications with album art
4. KDE/GNOME lock screen integration

### Phase 2: Music Discovery Foundation
1. Basic recommendation engine
2. Smart playlist creation system
3. Smart suggestions panel
4. Mood-based categorization

### Phase 3: Advanced Discovery Features
1. Visual music exploration tools
2. Interactive genre mapping
3. Enhanced mood-based recommendations
4. Weather and time-aware suggestions

## 📝 Development Notes

### Maintaining Design Philosophy
- **Linux-First**: Leverage native Linux technologies and conventions
- **Contextual Intelligence**: Features that adapt to user behavior and preferences
- **Visual Polish**: Consistent theming and professional UI/UX design
- **Modular Architecture**: Clean separation of concerns with focused modules
- **Performance Focus**: Non-blocking operations and efficient resource usage

### Integration with Existing Features
- **Theme System**: All new features will support the existing 8-theme system
- **Contextual Panel**: Discovery features integrate with existing information display
- **Logging System**: Comprehensive logging for all new functionality
- **Configuration**: Extensions to existing config.json structure

---

*This roadmap reflects the current state after successful implementation of system tray integration, mini player mode, and smart album queueing. Features will continue to be implemented incrementally with thorough testing and documentation.* 