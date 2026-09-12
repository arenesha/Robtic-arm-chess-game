import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.dashboard import Dashboard

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

def main():
    setup_logging()
    app = QApplication(sys.argv)
    
    dashboard = Dashboard()
    dashboard.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
