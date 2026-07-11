import os

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and not file.startswith("search_"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if "create_sidebar" in line:
                            print(f"{path}:{i} - {line.strip()}")
            except Exception:
                pass
