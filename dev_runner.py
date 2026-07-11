import os
import sys
import time
import subprocess

def get_mtimes(paths):
    """Recursively collects last modification times for python files in monitored paths."""
    mtimes = {}
    for p in paths:
        if os.path.exists(p):
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for file in files:
                        if file.endswith('.py'):
                            full_path = os.path.join(root, file)
                            try:
                                mtimes[full_path] = os.path.getmtime(full_path)
                            except Exception:
                                pass
            else:
                try:
                    mtimes[p] = os.path.getmtime(p)
                except Exception:
                    pass
    return mtimes

def main():
    watch_paths = ['gui', 'models', 'simulation', 'optimization', 'data_handlers', 'main.py']
    print("[Dev Reloader] Starting live-reloader. Monitoring files for changes...")
    
    current_mtimes = get_mtimes(watch_paths)
    
    # Spawn main.py
    cmd = [sys.executable, 'main.py']
    process = subprocess.Popen(cmd)
    print(f"[Dev Reloader] Started app process (PID: {process.pid})")
    
    try:
        while True:
            time.sleep(1.0)
            
            # Check if child process has exited
            if process.poll() is not None:
                # If exited with 0, user closed it normally, so we exit as well
                if process.returncode == 0:
                    print("[Dev Reloader] App closed normally. Exiting...")
                    break
                else:
                    # If crashed, keep running the reloader so saving a fix restarts the app
                    time.sleep(1.0)
            
            # Check for file modifications
            new_mtimes = get_mtimes(watch_paths)
            changed = False
            for path, mtime in new_mtimes.items():
                if path not in current_mtimes or current_mtimes[path] != mtime:
                    changed = True
                    print(f"[Dev Reloader] File change detected: {path}")
                    break
            
            for path in current_mtimes:
                if path not in new_mtimes:
                    changed = True
                    print(f"[Dev Reloader] File deleted: {path}")
                    break
                    
            if changed:
                print("[Dev Reloader] Restarting GUI app...")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
                process = subprocess.Popen(cmd)
                current_mtimes = new_mtimes
                print(f"[Dev Reloader] Restarted app process (PID: {process.pid})")
                
    except KeyboardInterrupt:
        print("[Dev Reloader] Stopping reloader...")
        process.terminate()
        try:
            process.wait(timeout=2)
        except Exception:
            process.kill()

if __name__ == '__main__':
    main()
