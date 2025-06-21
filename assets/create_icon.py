#!/usr/bin/env python3
"""
Create a synthwave-style icon for Pyper music player
Neon electric blue soundwave in a circle - minimal and clean
"""

try:
    from PIL import Image, ImageDraw
    import os
    import math
    
    # Create a 128x128 icon
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Synthwave colors
    bg_color = (36, 27, 47, 255)  # Dark synthwave background
    circle_color = (0, 212, 255, 255)  # Electric blue (#00d4ff)
    wave_color = (0, 212, 255, 255)  # Same electric blue for soundwave
    
    # Draw circular background with dark synthwave color
    margin = 6
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=bg_color)
    
    # Draw neon electric blue circle outline (thicker for glow effect)
    outline_width = 3
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 outline=circle_color, width=outline_width)
    
    # Draw inner glow effect
    for i in range(2):
        inner_margin = margin + outline_width + i
        draw.ellipse([inner_margin, inner_margin, size-inner_margin, size-inner_margin], 
                     outline=(0, 212, 255, 80), width=1)
    
    # Draw soundwave in the center
    center_x, center_y = size // 2, size // 2
    wave_width = 60
    wave_height = 40
    
    # Create soundwave pattern - multiple sine waves of different amplitudes
    wave_start_x = center_x - wave_width // 2
    wave_end_x = center_x + wave_width // 2
    
    # Draw multiple soundwave lines with varying amplitudes
    wave_amplitudes = [8, 12, 16, 12, 8, 14, 10, 18, 6, 16, 8, 12]
    wave_frequencies = [0.3, 0.4, 0.5, 0.6, 0.7, 0.4, 0.8, 0.35, 0.9, 0.45, 0.6, 0.5]
    
    for i, (amplitude, frequency) in enumerate(zip(wave_amplitudes, wave_frequencies)):
        x_offset = i * 5 - 25  # Spread waves across width
        if wave_start_x + x_offset < wave_start_x or wave_start_x + x_offset > wave_end_x - 10:
            continue
            
        # Calculate wave points
        wave_points = []
        for x in range(10):  # 10 points per wave line
            wave_x = wave_start_x + x_offset + x
            wave_y = center_y + amplitude * math.sin(frequency * x * math.pi / 5)
            wave_points.extend([wave_x, wave_y])
        
        # Draw the wave line with thickness
        if len(wave_points) >= 4:
            for thickness in range(2):  # Draw thick lines
                offset_points = []
                for j in range(0, len(wave_points), 2):
                    if j + 1 < len(wave_points):
                        offset_points.extend([wave_points[j], wave_points[j+1] + thickness])
                
                if len(offset_points) >= 4:
                    try:
                        draw.line(offset_points, fill=wave_color, width=2)
                    except:
                        pass  # Skip if line drawing fails
    
    # Add some vertical lines for more soundwave effect
    for i in range(8):
        x = wave_start_x + i * 8
        height = [6, 10, 14, 18, 16, 12, 8, 10][i]
        draw.line([x, center_y - height, x, center_y + height], 
                 fill=wave_color, width=2)
    
    # Save multiple sizes for different use cases
    sizes_to_create = [
        (128, 'pyper-icon.png'),
        (64, 'pyper-icon-64.png'),
        (48, 'pyper-icon-48.png'),
        (32, 'pyper-icon-32.png'),
        (16, 'pyper-icon-16.png')
    ]
    
    for icon_size, filename in sizes_to_create:
        if icon_size != size:
            # Resize the image
            resized_img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        else:
            resized_img = img
        
        icon_path = os.path.join(os.path.dirname(__file__), filename)
        resized_img.save(icon_path, 'PNG')
        print(f"Icon created at: {icon_path} ({icon_size}x{icon_size})")
    
    # Also create an ICO file for Windows compatibility
    try:
        ico_path = os.path.join(os.path.dirname(__file__), 'pyper-icon.ico')
        img.save(ico_path, 'ICO', sizes=[(128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"ICO file created at: {ico_path}")
    except:
        print("ICO creation failed, but PNG icons were created successfully")
    
except ImportError:
    print("PIL (Pillow) not available. Install with: pip install Pillow")
    print("Using default system icon instead.")
except Exception as e:
    print(f"Error creating icon: {e}")
    print("Using default system icon instead.") 