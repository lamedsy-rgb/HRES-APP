with open("gui/app.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if "nav_buttons" in line:
            print(f"Line {i}: {line.strip()}")
