Got it. Here are the requested edits incorporated into a revised `README.md`.

-----

# Pyper - A Modern Navidrome Music Player

Pyper is a clean, modern desktop music player built with Python, designed for seamless Browse and playback from a [Navidrome](https://www.navidrome.org/) music server. It features a fast, multi-pane interface for intuitive library exploration and is built to be lightweight and easy to use.

The entire application is designed to run on Linux and uses the powerful PyQt6 framework for its user interface, styled with `qt-material` for a modern aesthetic without the need for custom image assets.

*(Note: Screenshot shows default theme. Other themes available.)*

## Features

  * **Three-Pane Browser:** Intuitively drill-down through your music library. The panes are configurable to browse by:
      * Pane 1: Category (Artists, Albums, Playlists)
      * Pane 2: Items (e.g., List of all artists)
      * Pane 3: Sub-Items (e.g., Albums for the selected artist)
  * **Linux First:** Designed and tested for a native experience on Linux distributions.
  * **Album & Artist Art:** Displays the cover art for the currently playing album and for artist selections where available.
  * **Scrobbling via Navidrome:** Pyper reports played tracks back to your Navidrome server. If you have a scrobbling service (like Last.fm) configured in Navidrome, your plays will be logged automatically.
  * **Song Queueing:** Don't want to create a whole playlist? Just double-click a song or album to add it to the playback queue.
  * **Library Refresh:** A dedicated refresh button to pull the latest updates from your Navidrome server, ensuring new music is always available.
  * **Modern Theming:** Ships with several pre-configured themes to change the look and feel instantly. No complex skinning required.

## Getting Started

Follow these instructions to get Pyper running on your local machine.

### Prerequisites

  * Python 3.7+
  * A running Navidrome server instance (with user accounts configured).

### Installation

#### For Manjaro/Arch Linux:

1.  **Clone the repository (or save the Python script):**
    ```bash
    git clone https://github.com/your-username/pyper.git
    cd pyper
    ```
2.  **Install system packages:**
    ```bash
    sudo pacman -S python-pyqt6 python-requests python-pipx
    ```
3.  **Install remaining Python packages:**
    ```bash
    pip install --break-system-packages py-sonic qt-material
    ```

#### For other Linux distributions:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pyper.git
    cd pyper
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv pyper-venv
    source pyper-venv/bin/activate
    ```
3.  **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before launching the application, you must configure it to connect to your Navidrome server. Open the Python script (`pyper.py`) and edit the following lines:

```python
# --- Configuration ---
NAVIDROME_URL = "http://your-navidrome-server.com" # <--- IMPORTANT: Include http/https
NAVIDROME_USER = "your-username"                 # <--- IMPORTANT
NAVIDROME_PASS = "your-password"                 # <--- IMPORTANT
```

## Usage

1.  **Run the application:**
    ```bash
    python pyper.py
    ```
    
    Or use the provided launch script:
    ```bash
    ./run-pyper.sh
    ```
2.  **Browse:**
      * Select a category ("Artists", "Albums", "Playlists") in the first pane.
      * The second pane will populate with the corresponding items.
      * Selecting an item in the second pane will populate the third pane with related albums or songs.
3.  **Queueing Songs:**
      * Navigate to a list of songs in the third pane (by selecting an album or playlist).
      * Double-click an item to add all songs from that album/playlist to the main playback queue below.
      * Double-click a single song in the queue to begin playback.
4.  **Refreshing the Library:**
      * Click the "Refresh" button at any time to discard the local cache and fetch the latest library information from your Navidrome server.

## Theming

Pyper includes a selection of themes powered by `qt-material`. You can easily change the active theme by modifying one line in the script.

Find this line in the `if __name__ == '__main__':` block:

```python
# Apply a modern, clean theme
apply_stylesheet(app, theme='dark_teal.xml')
```

Change the `theme` parameter to any of the pre-configured options below.

#### Included Themes:

  * **Vintage IBM (`light_yellow.xml`)**: A retro theme with a patina'd, off-yellow background reminiscent of classic 1980s computer hardware.
  * **Synthwave (`dark_purple.xml`)**: A stylish theme with deep purples and pink highlights, perfect for a synthwave aesthetic.
  * **Oceanic (`dark_blue.xml`)**: A clean and classic dark theme with blue accents.
  * **Forest (`dark_teal.xml`)**: The default theme, featuring a pleasant dark green/teal look.
  * **Light (`light_blue.xml`)**: A crisp and clean light theme for daytime use.