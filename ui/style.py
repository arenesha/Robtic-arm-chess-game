# ui/style.py

def get_stylesheet():
    return """
    QMainWindow {
        background-color: #121212;
        color: #E0E0E0;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    
    QWidget {
        background-color: transparent;
        color: #E0E0E0;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    
    QGroupBox {
        border: 1px solid #333333;
        border-radius: 8px;
        margin-top: 1.5ex;
        background-color: #1E1E1E;
        font-weight: bold;
        color: #FFFFFF;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
        color: #3498DB;
    }
    
    QLabel {
        font-size: 14px;
        color: #CCCCCC;
    }
    
    QPushButton {
        background-color: #3498DB;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 14px;
    }
    
    QPushButton:hover {
        background-color: #2980B9;
    }
    
    QPushButton:pressed {
        background-color: #1C5980;
    }
    
    QPushButton:disabled {
        background-color: #555555;
        color: #888888;
    }
    
    QRadioButton {
        font-size: 14px;
        color: #CCCCCC;
    }
    
    QRadioButton::indicator {
        width: 14px;
        height: 14px;
        border-radius: 7px;
        border: 2px solid #555555;
        background-color: #1E1E1E;
    }
    
    QRadioButton::indicator:checked {
        border: 2px solid #3498DB;
        background-color: #3498DB;
    }
    """
