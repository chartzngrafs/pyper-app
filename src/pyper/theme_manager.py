"""
Theme Manager Module for Pyper Music Player
Handles application themes and styling
"""

import os
import json
import logging
from qt_material import apply_stylesheet

# Get logger
logger = logging.getLogger('Pyper')


class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'themes')
        self.current_theme = None
        self.available_themes = self.load_available_themes()
        
    def load_available_themes(self):
        """Load all available theme definitions"""
        themes = {}
        
        # Add qt-material themes
        qt_themes = {
            'dark_teal': {'name': 'Dark Teal (qt-material)', 'qt_theme': 'dark_teal.xml'},
            'dark_purple': {'name': 'Dark Purple (qt-material)', 'qt_theme': 'dark_purple.xml'},
            'dark_amber': {'name': 'Dark Amber (qt-material)', 'qt_theme': 'dark_amber.xml'},
            'dark_blue': {'name': 'Dark Blue (qt-material)', 'qt_theme': 'dark_blue.xml'},
            'light_teal': {'name': 'Light Teal (qt-material)', 'qt_theme': 'light_teal.xml'},
            'light_blue': {'name': 'Light Blue (qt-material)', 'qt_theme': 'light_blue.xml'}
        }
        themes.update(qt_themes)
        
        # Load custom themes from JSON files
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_id = filename[:-5]  # Remove .json extension
                    try:
                        with open(os.path.join(self.themes_dir, filename), 'r') as f:
                            theme_data = json.load(f)
                            themes[theme_id] = theme_data
                    except Exception as e:
                        logger.error(f"Failed to load theme {filename}: {e}")
        
        return themes
    
    def get_theme_list(self):
        """Get list of theme names for menu"""
        return [(theme_id, theme_data.get('name', theme_id)) for theme_id, theme_data in self.available_themes.items()]
    
    def apply_theme(self, app, theme_id):
        """Apply a theme to the application"""
        if theme_id not in self.available_themes:
            logger.error(f"Theme {theme_id} not found")
            return False
            
        theme_data = self.available_themes[theme_id]
        
        try:
            # Check if it's a qt-material theme
            if 'qt_theme' in theme_data:
                apply_stylesheet(app, theme=theme_data['qt_theme'])
                logger.info(f"Applied qt-material theme: {theme_data['name']}")
            else:
                # Apply custom theme
                self.apply_custom_theme(app, theme_data)
                logger.info(f"Applied custom theme: {theme_data['name']}")
            
            self.current_theme = theme_id
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply theme {theme_id}: {e}")
            return False
    
    def get_contrasting_text_color(self, background_color):
        """Get a contrasting text color (black or white) based on background color"""
        # Remove # if present
        bg_color = background_color.lstrip('#')
        
        # Convert to RGB
        try:
            r = int(bg_color[0:2], 16)
            g = int(bg_color[2:4], 16)
            b = int(bg_color[4:6], 16)
            
            # Calculate luminance using the relative luminance formula
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Return black text for light backgrounds, white text for dark backgrounds
            return '#000000' if luminance > 0.5 else '#FFFFFF'
        except:
            # Fallback to white if color parsing fails
            return '#FFFFFF'
    
    def apply_custom_theme(self, app, theme_data):
        """Apply a custom theme with CSS styling"""
        colors = theme_data.get('colors', {})
        
        # Create comprehensive stylesheet
        stylesheet = f"""
        QMainWindow {{
            background-color: {colors.get('background', '#212121')};
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QWidget {{
            background-color: {colors.get('background', '#212121')};
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QPushButton {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
            min-width: 60px;
            min-height: 30px;
        }}
        
        QPushButton:hover {{
            background-color: {colors.get('hover', '#616161')};
            border: 1px solid {colors.get('primary', '#009688')};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.get('pressed', '#757575')};
        }}
        
        QListWidget {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            selection-background-color: {colors.get('primary', '#009688')};
        }}
        
        QListWidget::item {{
            padding: 5px;
            border: none;
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QListWidget::item:hover {{
            background-color: {colors.get('hover', '#616161')};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors.get('border', '#757575')};
            background-color: {colors.get('surface', '#424242')};
        }}
        
        QTabBar::tab {{
            background-color: {colors.get('surface_light', '#616161')};
            color: {colors.get('text_secondary', '#BDBDBD')};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors.get('hover', '#616161')};
        }}
        
        QLineEdit {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {colors.get('primary', '#009688')};
        }}
        
        QLabel {{
            color: {colors.get('text', '#FFFFFF')};
        }}
        
        QProgressBar {{
            background-color: {colors.get('surface', '#424242')};
            border: 1px solid {colors.get('border', '#757575')};
            border-radius: 5px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.get('primary', '#009688')};
            border-radius: 4px;
        }}
        
        QScrollArea {{
            background-color: {colors.get('surface', '#424242')};
            border: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenu {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenu::item {{
            padding: 5px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        
        QMenuBar {{
            background-color: {colors.get('surface', '#424242')};
            color: {colors.get('text', '#FFFFFF')};
            border-bottom: 1px solid {colors.get('border', '#757575')};
        }}
        
        QMenuBar::item {{
            padding: 5px 10px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.get('primary', '#009688')};
            color: {self.get_contrasting_text_color(colors.get('primary', '#009688'))};
        }}
        """
        
        # Add special styling for now playing label if the color is defined
        if 'now_playing' in colors:
            # Store the color for dynamic styling
            self.now_playing_color = colors['now_playing']
        else:
            self.now_playing_color = None
            
        app.setStyleSheet(stylesheet)
    
    def apply_element_specific_styling(self, main_window=None):
        """Apply theme-specific styling to individual elements"""
        if hasattr(self, 'now_playing_color') and self.now_playing_color and main_window:
            # Apply the special now playing color if available
            if hasattr(main_window, 'now_playing_label'):
                main_window.now_playing_label.setStyleSheet(f"color: {self.now_playing_color}; font-weight: bold;")
        
        # Apply theme colors to album grid if available
        if main_window and hasattr(main_window, 'album_grid') and self.current_theme:
            current_theme_data = self.available_themes.get(self.current_theme, {})
            if 'colors' in current_theme_data:
                main_window.album_grid.apply_theme_colors(current_theme_data['colors'])
                
                # Apply theme colors to subitems container to maintain border
                if hasattr(main_window, 'subitems_container'):
                    surface_color = current_theme_data['colors'].get('surface', '#2a2139')
                    border_color = current_theme_data['colors'].get('border', '#495495')
                    main_window.subitems_container.setStyleSheet(f"""
                        QWidget {{
                            border: 1px solid {border_color};
                            background-color: transparent;
                        }}
                    """)
    
    def save_theme_preference(self, theme_id):
        """Save theme preference to config"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.json')
            
            # Read current config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update theme
            if 'ui' not in config:
                config['ui'] = {}
            config['ui']['theme'] = theme_id
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Saved theme preference: {theme_id}")
            
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}") 