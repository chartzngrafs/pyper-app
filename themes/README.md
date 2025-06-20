# Pyper Custom Themes

This directory contains custom theme definitions for Pyper. The theming system includes automatic text contrast calculation to ensure readability across all themes.

## Available Custom Themes

1. **Dark Teal** - Default dark teal theme with professional appearance
2. **Cobalt Blue** - Deep cobalt blue with electric accents
3. **IBM Patina Yellow** - Warm patina yellow inspired by IBM vintage computing
4. **Hacker Green** - Matrix-inspired green terminal theme
5. **Dracula** - Dark theme with purple accents inspired by Dracula
6. **Tokyo Midnight** - Dark blue theme with neon accents inspired by Tokyo nights
7. **Monochrome** - Clean black, white, and gray theme
8. **Synthwave '84** - Authentic 80s synthwave theme with neon pink (#f92aad), green (#72f1b8), and yellow (#fede5d)

## Theme Features

### Automatic Text Contrast
Pyper automatically calculates the optimal text color (black or white) for selections and highlighted elements based on the background color's luminance. This ensures:
- **Perfect Readability**: Text is always visible regardless of theme colors
- **Accessibility**: Proper contrast ratios for better accessibility
- **Consistency**: Uniform text visibility across all UI elements

### Real-time Switching
- Change themes instantly via **View → Themes** menu
- No restart required
- Theme preference is automatically saved

## Creating Custom Themes

To create a custom theme, create a new JSON file in this directory with the following structure:

```json
{
    "name": "Your Theme Name",
    "description": "Description of your theme",
    "colors": {
        "primary": "#HEX_COLOR",
        "primary_light": "#HEX_COLOR",
        "primary_dark": "#HEX_COLOR",
        "secondary": "#HEX_COLOR",
        "background": "#HEX_COLOR",
        "surface": "#HEX_COLOR",
        "surface_light": "#HEX_COLOR",
        "text": "#HEX_COLOR",
        "text_secondary": "#HEX_COLOR",
        "accent": "#HEX_COLOR",
        "border": "#HEX_COLOR",
        "hover": "#HEX_COLOR",
        "pressed": "#HEX_COLOR",
        "success": "#HEX_COLOR",
        "warning": "#HEX_COLOR",
        "error": "#HEX_COLOR"
    }
}
```

## Color Definitions

- **primary**: Main theme color (used for selections, active elements) - *Text contrast is automatically calculated*
- **primary_light**: Lighter variant of primary color
- **primary_dark**: Darker variant of primary color
- **secondary**: Secondary accent color
- **background**: Main background color
- **surface**: Background color for panels and widgets
- **surface_light**: Lighter surface color for tabs and elevated elements
- **text**: Primary text color
- **text_secondary**: Secondary text color (less prominent)
- **accent**: Accent color for highlights
- **border**: Border color for UI elements
- **hover**: Color when hovering over interactive elements
- **pressed**: Color when pressing buttons
- **success**: Color for success messages
- **warning**: Color for warning messages
- **error**: Color for error messages

## Using Your Theme

1. Save your theme JSON file in this directory
2. Restart Pyper (or the theme will be available after the next restart)
3. Go to **View → Themes** in the menu bar
4. Select your custom theme

## Tips for Theme Creation

- **Don't worry about text contrast**: The system automatically handles text colors for selections
- Use a color palette generator or existing design systems for inspiration
- Ensure sufficient contrast between regular text and background colors
- Test your theme with different UI elements
- Consider both light and dark variants if desired
- Use consistent color relationships (e.g., hover should be lighter/darker than base)
- **Bright colors work great**: The automatic contrast system handles bright primary colors perfectly

## Special Theme Notes

### Synthwave '84
This theme uses authentic colors from the legendary VS Code Synthwave '84 theme:
- Background: `#241b2f` (deep purple-black)
- Primary: `#f92aad` (neon pink) - automatically gets black text for perfect contrast
- Secondary: `#72f1b8` (neon green)
- Accent: `#fede5d` (neon yellow)
- Text: `#a599e9` (light purple)

### Monochrome
Perfect for professional environments with clean black, white, and gray colors. The automatic contrast system ensures white selections show black text for perfect readability.

## Qt-Material Themes

Pyper also supports built-in qt-material themes:
- Dark Teal, Dark Purple, Dark Amber, Dark Blue
- Light Teal, Light Blue

These are automatically available and don't require JSON files. 