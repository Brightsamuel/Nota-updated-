from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from io import BytesIO
from PIL import Image, ImageDraw

def create_gradient_texture(color1, color2, width=100, height=100):
    """
    Create a vertical gradient texture from color1 to color2.
    
    Args:
        color1 (tuple): The color at the top (r, g, b, a)
        color2 (tuple): The color at the bottom (r, g, b, a)
        width (int): Width of the texture
        height (int): Height of the texture
        
    Returns:
        Kivy texture object
    """
    # Create a new RGBA image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Convert colors to 0-255 range
    color1_255 = tuple(int(c * 255) for c in color1)
    color2_255 = tuple(int(c * 255) for c in color2)
    
    # Draw the gradient
    for y in range(height):
        # Calculate color for this line
        r = int(color1_255[0] * (height - y) / height + color2_255[0] * y / height)
        g = int(color1_255[1] * (height - y) / height + color2_255[1] * y / height)
        b = int(color1_255[2] * (height - y) / height + color2_255[2] * y / height)
        a = int(color1_255[3] * (height - y) / height + color2_255[3] * y / height)
        
        # Draw a line with this color
        draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    # Convert the PIL image to bytes
    data = BytesIO()
    img.save(data, format='PNG')
    data.seek(0)
    
    # Create a Kivy texture
    texture = CoreImage(BytesIO(data.read()), ext='png').texture
    
    return texture