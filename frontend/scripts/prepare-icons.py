"""Regenerate runtime WebP files from preserved PNG masters. Requires Pillow."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
source = root / 'design/icons/originals'
output = root / 'public/icons/welfare'
output.mkdir(parents=True, exist_ok=True)
for path in sorted(source.glob('*.png')):
    with Image.open(path) as image:
        image = image.convert('RGBA')
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        image.save(output / f'{path.stem}.webp', 'WEBP', quality=90, method=6)
    print(f'{path.stem}.webp')
