with open("gui/app.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        for term in ["appearance_mode_optionemenu", "language_optionmenu", "save_session_btn", "load_session_btn"]:
            if term in line:
                print(f"Line {i}: {line.strip()}")
