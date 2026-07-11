import os
from PIL import Image

src = r"C:\Users\Mhmd2\.gemini\antigravity\brain\227ca93e-503d-4919-8daa-3dfed8560151\hres_logo_clean_1783517066101.jpg"
dst_dir = r"C:\Users\Mhmd2\OneDrive\Bureau\RE\CAPSTONE\CAPAPP\gui"

ico_path = os.path.join(dst_dir, "logo.ico")
png_path = os.path.join(dst_dir, "logo.png")

print(f"Loading generated logo from: {src}")
img = Image.open(src)

print(f"Saving multi-size Windows icon to: {ico_path}")
img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print(f"Saving PNG image to: {png_path}")
img.save(png_path, format="PNG")
print("Conversion completed successfully!")
