import os
import sys
import logging

# Setup logging to write uncaught exceptions to 'app_error.log'
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_error.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = exception_handler

def main():
    try:
        logging.info("Starting HRES Optimizer GUI Application...")
        from gui.app import Application
        app = Application()
        app.mainloop()
    except Exception as e:
        logging.critical("Failed to start application:", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
