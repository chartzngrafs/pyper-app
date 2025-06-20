#!/bin/bash

# Pyper - Install Desktop Shortcut Script
# This script creates shortcuts for Pyper on Linux

echo "🎵 Installing Pyper Desktop Shortcut..."

# Get the current directory (where Pyper is located)
PYPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Pyper directory: $PYPER_DIR"

# Create applications directory if it doesn't exist
mkdir -p ~/.local/share/applications

# Update the desktop file with correct paths
sed "s|/home/kevin/coding-playground/pyper-app|$PYPER_DIR|g" assets/pyper.desktop > ~/.local/share/applications/pyper.desktop

# Make it executable
chmod +x ~/.local/share/applications/pyper.desktop

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database ~/.local/share/applications
    echo "✅ Desktop database updated"
else
    echo "⚠️ update-desktop-database not found, you may need to log out/in for the shortcut to appear"
fi

echo ""
echo "🎉 Desktop shortcut installed successfully!"
echo ""
echo "You can now:"
echo "  • Find 'Pyper' in your application menu"
echo "  • Pin it to your taskbar/dock"
echo "  • Create a desktop shortcut by copying:"
echo "    cp ~/.local/share/applications/pyper.desktop ~/Desktop/"
echo ""

# Offer to create desktop shortcut
if [ -d "$HOME/Desktop" ]; then
    read -p "Create desktop shortcut? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp ~/.local/share/applications/pyper.desktop ~/Desktop/
        chmod +x ~/Desktop/pyper.desktop
        echo "✅ Desktop shortcut created!"
    fi
fi 