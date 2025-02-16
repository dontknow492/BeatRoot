from PIL import Image, ImageChops
import requests
from io import BytesIO
from collections import defaultdict

def get_border_color(img):
    """Determine border color by sampling edges"""
    width, height = img.size
    samples = []
    
    # Sample points along all edges
    step = max(1, min(width, height) // 20)  # Dynamic step size
    
    # Top and bottom edges
    for x in range(0, width, step):
        samples.append(img.getpixel((x, 0)))
        samples.append(img.getpixel((x, height-1)))
    
    # Left and right edges
    for y in range(0, height, step):
        samples.append(img.getpixel((0, y)))
        samples.append(img.getpixel((width-1, y)))
    
    # Find most common color
    color_counts = defaultdict(int)
    for color in samples:
        color_counts[color] += 1
    return max(color_counts, key=lambda k: color_counts[k])

def remove_borders(image_data, padding=3, threshold=25):
    """Improved border removal with error handling and padding"""

    try:
        img = Image.open(BytesIO(image_data)).convert('RGB')
    except Exception as e:
        print(f"Image processing error: {e}")
        return None

    border_color = get_border_color(img)
    bg = Image.new(img.mode, img.size, border_color)
    
    # Calculate difference with threshold
    diff = ImageChops.difference(img, bg)
    diff = diff.convert('L').point(lambda p: 255 if p > threshold else 0)
    
    bbox = diff.getbbox()
    if not bbox:
        print("No borders detected")
        return img

    # Apply padding with boundary checks
    left, upper, right, lower = bbox
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(img.width, right + padding)
    lower = min(img.height, lower + padding)
    
    
    return img.crop((left, upper, right, lower))