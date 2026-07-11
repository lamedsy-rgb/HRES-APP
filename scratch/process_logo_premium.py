import os
import numpy as np
from PIL import Image

src = r"C:\Users\Mhmd2\.gemini\antigravity\brain\227ca93e-503d-4919-8daa-3dfed8560151\hres_logo_bw_blue_1783518104443.jpg"
dst_dir = r"C:\Users\Mhmd2\OneDrive\Bureau\RE\CAPSTONE\CAPAPP\gui"

ico_path = os.path.join(dst_dir, "logo.ico")
png_path = os.path.join(dst_dir, "logo.png")

print(f"Loading premium logo from: {src}")
img = Image.open(src).convert("RGBA")
data = np.array(img)

# Take the top-left pixel as the background color reference
bg_key = data[0, 0][:3]
print(f"Detected background key: {bg_key}")

# Calculate distance of each pixel to the background color
distances = np.linalg.norm(data[:, :, :3] - bg_key, axis=2)

# Make background pixels transparent (threshold of 45 covers compression artifacts)
threshold = 45
data[distances < threshold] = [0, 0, 0, 0]

# Save the transparent PNG for internal CTkImage top bar rendering
transparent_img = Image.fromarray(data)
print(f"Saving transparent PNG logo to: {png_path}")
transparent_img.save(png_path, format="PNG")

# For the Windows .ico file, set a solid premium dark color (43, 43, 43) matching Tkinter's dark theme
# so the taskbar icon doesn't have white transparent pixels artifacts on Windows
ico_data = np.array(img)
ico_distances = np.linalg.norm(ico_data[:, :, :3] - bg_key, axis=2)
ico_data[ico_distances < threshold] = [43, 43, 43, 255] # #2b2b2b
ico_img = Image.fromarray(ico_data).convert("RGB")

print(f"Saving Windows taskbar icon to: {ico_path}")
ico_img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Premium logo processing complete!")
