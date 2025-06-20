#!/usr/bin/env python3
"""
Create a simple icon for Pyper music player
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # Create a 128x128 icon
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a circular background
    margin = 8
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(139, 92, 246, 255),  # Purple color
                 outline=(255, 255, 255, 255), width=3)
    
    # Draw musical note symbol
    center_x, center_y = size // 2, size // 2
    
    # Try to use a larger font for the musical note
    try:
        font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 48)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
    
    # Draw musical note
    text = "♪"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    draw.text((center_x - text_width//2, center_y - text_height//2), 
              text, fill=(255, 255, 255, 255), font=font)
    
    # Save the icon
    icon_path = os.path.join(os.path.dirname(__file__), 'pyper-icon.png')
    img.save(icon_path, 'PNG')
    print(f"Icon created at: {icon_path}")
    
except ImportError:
    print("PIL (Pillow) not available. Install with: pip install Pillow")
    print("Using default system icon instead.")
except Exception as e:
    print(f"Error creating icon: {e}")
    print("Using default system icon instead.") 