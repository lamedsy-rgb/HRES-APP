import os
import sys
import subprocess
import shutil
import logging
import tkintermapview

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_app():
    logger.info("Starting HRES Optimizer build process...")
    
    # 1. Clean previous build files if they exist
    dirs_to_clean = ['build', 'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            logger.info(f"Cleaning existing directory: {d}")
            try:
                shutil.rmtree(d)
            except Exception as e:
                logger.warning(f"Could not remove directory {d}: {e}")
                
    files_to_clean = ['HRES_Optimizer.spec']
    for f in files_to_clean:
        if os.path.exists(f):
            logger.info(f"Cleaning existing file: {f}")
            try:
                os.remove(f)
            except Exception as e:
                logger.warning(f"Could not remove file {f}: {e}")

    # 2. Dynamically locate customtkinter path
    try:
        import customtkinter
        customtkinter_dir = os.path.dirname(customtkinter.__file__)
        logger.info(f"Located customtkinter library at: {customtkinter_dir}")
    except ImportError:
        logger.error("customtkinter library is not installed. Please run 'pip install -r requirements.txt'")
        sys.exit(1)

    # Dynamically locate tkintermapview path
    try:
        tkintermapview_dir = os.path.dirname(tkintermapview.__file__)
        logger.info(f"Located tkintermapview library at: {tkintermapview_dir}")
    except Exception as e:
        logger.error(f"Could not locate tkintermapview: {e}")
        sys.exit(1)

    # 3. Construct PyInstaller command
    # Windows uses semicolon ';' separator for add-data
    customtkinter_add_data = f"{customtkinter_dir};customtkinter"
    tkintermapview_add_data = f"{tkintermapview_dir};tkintermapview"
    cmd = [
        "pyinstaller",
        "--clean",
        "--onedir",
        "--console",
        "--add-data", customtkinter_add_data,
        "--add-data", tkintermapview_add_data,
        "--name", "HRES_Optimizer",
        "main.py"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # 4. Execute build
    try:
        # Run PyInstaller
        # Note: we run it synchronously and capture output for debugging
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("PyInstaller completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller failed with exit code: {e.returncode}")
        logger.error(f"Stderr:\n{e.stderr}")
        logger.error(f"Stdout:\n{e.stdout}")
        sys.exit(e.returncode)

    # 5. Verify the output executable exists
    exe_path = os.path.join("dist", "HRES_Optimizer", "HRES_Optimizer.exe")
    if os.path.exists(exe_path):
        logger.info(f"Success! Standalone executable successfully built at: {os.path.abspath(exe_path)}")
    else:
        logger.error(f"Expected executable not found at {exe_path}")
        sys.exit(1)

if __name__ == '__main__':
    build_app()
