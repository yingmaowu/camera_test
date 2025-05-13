from PIL import Image, ImageDraw

def overlay_grid(image_path, output_path=None, rows=3, cols=3, line_color=(255, 0, 0), line_width=2):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    dx = width // cols
    dy = height // rows
    for i in range(1, cols):
        draw.line([(i * dx, 0), (i * dx, height)], fill=line_color, width=line_width)
    for j in range(1, rows):
        draw.line([(0, j * dy), (width, j * dy)], fill=line_color, width=line_width)
    if output_path:
        img.save(output_path)
    else:
        img.save(image_path)
