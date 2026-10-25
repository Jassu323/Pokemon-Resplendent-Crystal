"""Contact sheet of captured display frames, not altered cartridge graphics."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
cases = (
    ('left-0', 'before', '004', '008', '015', '021', 'after'),
    ('left-1', 'before', '004', '008', '010', '013', 'after'),
)
canvas = Image.new('RGB', (6 * 332, 2 * 320), '#e8e8e8')
draw = ImageDraw.Draw(canvas)
for row, (case, *frames) in enumerate(cases):
    for col, frame in enumerate(frames):
        path = root / f'{case}-{frame}.ppm'
        image = Image.open(path).convert('RGB').resize((320, 288), Image.Resampling.NEAREST)
        x, y = col * 332 + 6, row * 320 + 26
        canvas.paste(image, (x, y))
        draw.text((x, y - 18), f'{case}: {frame}', fill='black')
canvas.save(root / 'pouch-transitions.png')
