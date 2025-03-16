#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from gui import MainWindow
from utils.error_handling import logger

def main():
    """Main entry point for the application"""
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Set application style
        
        # Set application name and organization
        app.setApplicationName("Video Steganography Tool")
        app.setOrganizationName("VideoSteganography")
        
        # Check if assets directory exists for icons
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
