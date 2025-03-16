import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QApplication,
    QLabel, QStatusBar, QAction, QFileDialog, QVBoxLayout,
    QWidget
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize

from gui.encode_tab import EncodeTab
from gui.decode_tab import DecodeTab
from utils.error_handling import ErrorHandler
from steganography import LSBSteganography, VideoInVideoSteganography

class MainWindow(QMainWindow):
    """
    Main application window for Video Steganography Tool
    """
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        # Set window properties
        self.setWindowTitle("Video Steganography Tool")
        self.setMinimumSize(800, 600)
        
        # Create central widget and tab container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create header with logo
        self.create_header()
        
        # Create tabs
        self.create_tabs()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create menu
        self.create_menu()
        
        # Center the window
        self.center()
        
    def create_header(self):
        """Create header with logo and title"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        
        # Title
        title_label = QLabel("Video Steganography Tool")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        
        # Description
        desc_label = QLabel("Hide and extract secret messages in videos")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        
        self.layout.addWidget(header_widget)
        
    def create_tabs(self):
        """Create and configure tab widgets"""
        self.tabs = QTabWidget()
        
        # Create encode tab
        self.encode_tab = EncodeTab(self)
        self.tabs.addTab(self.encode_tab, "Encode Message")
        
        # Create decode tab
        self.decode_tab = DecodeTab(self)
        self.tabs.addTab(self.decode_tab, "Decode Message")
        
        # Add tabs to main layout
        self.layout.addWidget(self.tabs)
        
    def create_menu(self):
        """Create application menu"""
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Open video action
        open_action = QAction("Open Video", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_video)
        file_menu.addAction(open_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def open_video(self):
        """Open video file dialog"""
        try:
            file_filter = "Video files (*.mp4 *.avi *.mov *.mkv);;All files (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Video File", "", file_filter
            )
            
            if file_path:
                # Determine which tab is currently active
                current_index = self.tabs.currentIndex()
                
                if current_index == 0:  # Encode tab
                    self.encode_tab.set_input_video(file_path)
                else:  # Decode tab
                    self.decode_tab.set_input_video(file_path)
                    
                self.statusBar.showMessage(f"Opened: {os.path.basename(file_path)}")
        except Exception as e:
            ErrorHandler.handle_error(self, e, "Video Open Error", "Failed to open video file")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Video Steganography Tool",
            """<h2>Video Steganography Tool</h2>
            <p>A tool for hiding and extracting secret messages in videos.</p>
            <p>Supports LSB and DCT steganography methods.</p>
            <p><b>Version:</b> 0.1.0</p>"""
        )
    
    def center(self):
        """Center window on screen"""
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos()
        )
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, "Exit Confirmation",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore() 