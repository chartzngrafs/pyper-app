# Pyper - A Modern Navidrome Music Player

A feature-rich, Linux-first music player application designed specifically for Navidrome servers. Built with PyQt6 and featuring a clean, modern interface with robust search capabilities and intuitive workflow.

## ✨ Features

- **🐧 Linux-First Design**: Optimized for Linux desktop environments
- **🔍 Powerful Search**: Search across artists, albums, and songs with dedicated search tab
- **🎯 Tabbed Interface**: Browse, Search, and Queue tabs for organized workflow
- **🎨 Album Art Support**: Automatic album artwork display with proper scaling
- **📋 Queue Management**: Full playback queue with individual track management and Clear Queue functionality
- **🎵 Scrobbling**: Last.fm compatible scrobbling through Navidrome
- **🌙 Modern Theming**: Dark theme with qt-material styling and purple accents
- **🖱️ Context Menus**: Right-click options throughout the interface
- **⚡ Smart Playback**: Double-click anywhere to add and play immediately

## 📋 Requirements

- Python 3.8+
- PyQt6
- Navidrome server (configured and running)
- Linux desktop environment (tested on Manjaro/Arch)

## 🚀 Installation

### For Manjaro/Arch Linux:

1. **Install system dependencies:**
   ```bash
   sudo pacman -S python-pyqt6 python-requests python-pipx
   ```

2. **Install Python packages:**
   ```bash
   pip install --break-system-packages py-sonic qt-material
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

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure and run as above**

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
        "password": "your_password"
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

## 🎵 Usage

### Navigation Structure
- **Browse Tab**: Navigate Artists → Albums → Songs hierarchy
- **Search Tab**: Find content across your entire library
- **Queue Tab**: Manage your playback queue

### Search Functionality
1. Type in the search bar at the top
2. Press Enter or click "Search"
3. Results appear in Artists | Albums | Songs columns
4. Double-click or right-click any result to play or queue

### Playback Controls
- **Double-click** any item to add to queue and start playing
- **Right-click** for context menu options:
  - "Add to Queue" - adds without playing
  - "Play Now" - adds to queue and starts playing immediately
- **Player Bar**: Compact controls with artwork, progress, and time

### Queue Management
- **Queue Tab**: Full queue view with clear button
- **Right-click** queue items for "Remove from Queue" or "Play Now"
- **Clear Queue** button in Queue tab to empty entire queue

### Album Artwork
- **Click artwork** in player to show detailed track info dialog
- Artwork automatically loads and scales properly
- Large artwork display in now playing dialog

## 🏗️ Project Structure

```
pyper-app/
├── src/
│   └── pyper/
│       ├── __init__.py        # Package initialization  
│       └── main.py            # Main application code
├── config/
│   ├── config.example.json    # Example configuration
│   └── config.json           # Your configuration (ignored by git)
├── docs/                     # Documentation
├── assets/                   # Assets and resources
├── pyper.py                  # Entry point script
├── requirements.txt          # Python dependencies
├── run-pyper.sh             # Launch script with config check
├── setup.py                 # Package setup
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## 🛠️ Troubleshooting

### Configuration Issues
```bash
# Check if config exists
ls -la config/config.json

# Validate JSON syntax
python -m json.tool config/config.json
```

### Connection Issues
- Verify Navidrome server is running and accessible
- Test by accessing Navidrome web interface first  
- Check URL format includes `http://` or `https://`
- Verify username and password are correct

### Audio Issues
- Ensure system has proper audio codecs installed
- Check that other audio applications work
- Verify Qt multimedia framework is installed

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

### Running from Source
```bash
# Install in development mode
pip install -e .

# Run with debug output
python -c "import sys; sys.path.insert(0, 'src'); from pyper.main import main; main()"
```

### Configuration Management
- Sensitive data is kept in `config/config.json` (gitignored)
- Example config shows required structure
- UI settings are also configurable

## 📄 License

Open source - feel free to modify and distribute.

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

### Development Guidelines
- Follow existing code style
- Test with different Navidrome configurations
- Update documentation for new features
- Keep sensitive data out of commits

---

**🎵 Enjoy your music with Pyper! A modern player for modern music lovers.**