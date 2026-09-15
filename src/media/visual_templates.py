"""
src/media/visual_templates.py - Original visual generation (maps, charts, timelines)
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from src.utils.logger import setup_logger
from src.config import PATHS

logger = setup_logger(__name__)


def create_timeline_image(events, width=1080, height=1920):
    """Create timeline visualization"""
    img = Image.new('RGB', (width, height), (15, 15, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        font_bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Title
    draw.text((width//2, 100), "TIMELINE", font=font_bold,
              fill=(255, 255, 255), anchor='mm')
    
    # Draw line
    line_x = 200
    draw.line([(line_x, 300), (line_x, height - 200)], fill=(100, 150, 255), width=6)
    
    # Draw events
    y_pos = 350
    for event in events[:5]:
        # Dot
        draw.ellipse([line_x - 15, y_pos - 15, line_x + 15, y_pos + 15],
                     fill=(255, 200, 0))
        
        # Text
        draw.text((line_x + 40, y_pos), str(event), font=font_small,
                  fill=(255, 255, 255), anchor='lm')
        
        y_pos += 250
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"timeline_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


def create_bar_chart(data, title="DATA", width=1080, height=1920):
    """Create bar chart visualization"""
    img = Image.new('RGB', (width, height), (15, 15, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        font_label = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
    
    # Title
    draw.text((width//2, 150), title, font=font_title,
              fill=(255, 255, 255), anchor='mm')
    
    # Bars
    if data:
        max_val = max(v for _, v in data) or 1
        bar_width = (width - 200) // len(data)
        x_start = 100
        base_y = height - 300
        max_bar_height = height - 700
        
        for i, (label, value) in enumerate(data[:6]):
            bar_h = int((value / max_val) * max_bar_height)
            x = x_start + i * bar_width + 20
            y = base_y - bar_h
            
            # Bar
            draw.rectangle([x, y, x + bar_width - 40, base_y],
                           fill=(100, 150, 255))
            
            # Label
            draw.text((x + (bar_width - 40)//2, base_y + 30), str(label),
                      font=font_label, fill=(255, 255, 255), anchor='mt')
            
            # Value
            draw.text((x + (bar_width - 40)//2, y - 30), str(value),
                      font=font_label, fill=(255, 200, 0), anchor='mb')
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"chart_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


def create_text_overlay(text, bg_color=(0, 0, 0, 180), width=1080, height=400):
    """Create text overlay with background"""
    img = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    words = text.split()
    lines = []
    current = ""
    
    for word in words:
        test = current + " " + word if current else word
        # Estimate width
        if len(test) * 30 > width - 100:
            lines.append(current)
            current = word
        else:
            current = test
    
    if current:
        lines.append(current)
    
    # Draw
    y_start = (height - len(lines) * 80) // 2
    for i, line in enumerate(lines[:4]):
        draw.text((width//2, y_start + i * 80), line, font=font,
                  fill=(255, 255, 255), anchor='mm')
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"overlay_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


def create_map_placeholder(country="USA", width=1080, height=1920):
    """Create simple map placeholder"""
    img = Image.new('RGB', (width, height), (15, 15, 30))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Simple globe representation
    center_x, center_y = width // 2, height // 2
    radius = 300
    
    draw.ellipse([center_x - radius, center_y - radius,
                  center_x + radius, center_y + radius],
                 outline=(100, 150, 255), width=8)
    
    # Country name
    draw.text((center_x, center_y + radius + 100), country.upper(),
              font=font, fill=(255, 255, 255), anchor='mm')
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"map_{random.randint(1, 999999)}.png")
    img.save(path)
    return path
