import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QProgressBar,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from steganography import LSBSteganography, DCTSteganography
from utils.video_handler import VideoHandler
from utils.error_handling import ErrorHandler

class DecodeThread(QThread):
    """Thread for decoding messages to avoid UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    
    def __init__(self, method, video_path):
        super().__init__()
        self.method = method
        self.video_path = video_path
    
    def run(self):
        try:
            # Update progress
            self.progress.emit(10)
            
            # Choose steganography method
            if self.method == "LSB":
                steg = LSBSteganography()
            else:  # DCT
                steg = DCTSteganography()
                
            # Update progress
            self.progress.emit(33)
                
            # Decode the message
            message = steg.extract_data(self.video_path)
            
            # Update progress
            self.progress.emit(100)
            
            # Emit result
            if message and message != "No hidden message found" and message != "Error extracting data":
                self.finished.emit(True, message)
            else:
                self.finished.emit(False, message)
        
        except Exception as e:
            self.finished.emit(False, str(e))

class DecodeTab(QWidget):
    """Tab for decoding secret messages from videos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.input_video_path = None
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # Video selection section
        video_group = QGroupBox("Input Video")
        video_layout = QVBoxLayout()
        
        # Input video selection
        input_layout = QHBoxLayout()
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setReadOnly(True)
        self.video_path_edit.setPlaceholderText("Select video with hidden message...")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_video)
        
        input_layout.addWidget(self.video_path_edit)
        input_layout.addWidget(browse_btn)
        
        # Video info display
        info_layout = QFormLayout()
        self.video_info_label = QLabel("No video selected")
        self.video_info_label.setWordWrap(True)
        
        info_layout.addRow("Video Details:", self.video_info_label)
        
        video_layout.addLayout(input_layout)
        video_layout.addLayout(info_layout)
        video_group.setLayout(video_layout)
        
        # Decoding options section
        options_group = QGroupBox("Decoding Options")
        options_layout = QFormLayout()
        
        # Steganography method
        self.method_combo = QComboBox()
        self.method_combo.addItems(["LSB", "DCT"])
        
        options_layout.addRow("Steganography Method:", self.method_combo)

        options_group.setLayout(options_layout)
        
        # Extracted message section
        message_group = QGroupBox("Extracted Message")
        message_layout = QVBoxLayout()
        
        # Message text area
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setPlaceholderText("Extracted message will appear here...")
        
        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        
        message_layout.addWidget(self.message_display)
        message_layout.addWidget(copy_btn)
        message_group.setLayout(message_layout)
        
        # Progress section
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.decode_btn = QPushButton("Decode Message")
        self.decode_btn.setEnabled(False)
        self.decode_btn.clicked.connect(self.decode_message)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.decode_btn)
        button_layout.addWidget(clear_btn)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(button_layout)
        
        # Add all components to main layout
        main_layout.addWidget(video_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(message_group)
        main_layout.addLayout(progress_layout)
        
        self.setLayout(main_layout)
    
    def browse_video(self):
        """Browse for input video file"""
        try:
            file_filter = "Video files (*.mp4 *.avi *.mov *.mkv);;All files (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Video with Hidden Message", "", file_filter
            )
            
            if file_path:
                self.set_input_video(file_path)
        except Exception as e:
            ErrorHandler.handle_error(self.parent, e, "Video Selection Error")
    
    def set_input_video(self, file_path):
        """Set input video path and update UI"""
        # Validate the video file
        if not VideoHandler.validate_video(file_path):
            ErrorHandler.show_error_message(
                self.parent, "Invalid Video", 
                "The selected file is not a valid video."
            )
            return
            
        self.input_video_path = file_path
        self.video_path_edit.setText(file_path)
        
        # Display video info
        self.display_video_info()
        
        # Enable decode button
        self.decode_btn.setEnabled(True)
    
    def display_video_info(self):
        """Display information about the selected video"""
        if not self.input_video_path:
            return
            
        try:
            info = VideoHandler.get_video_info(self.input_video_path)
            
            if "error" in info:
                self.video_info_label.setText(f"Error: {info['error']}")
                return
                
            # Format and display video information
            info_text = (
                f"Name: {info['file_name']}\n"
                f"Size: {info['file_size_mb']:.2f} MB\n"
                f"Resolution: {info['width']}x{info['height']}\n"
                f"Duration: {info['duration']:.2f} seconds\n"
                f"FPS: {info['fps']:.2f}"
            )
            
            self.video_info_label.setText(info_text)
            
        except Exception as e:
            ErrorHandler.log_exception(e, "Error displaying video info")
            self.video_info_label.setText("Error retrieving video information")
    
    def copy_to_clipboard(self):
        """Copy extracted message to clipboard"""
        text = self.message_display.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.parent.statusBar.showMessage("Message copied to clipboard")
        else:
            self.parent.statusBar.showMessage("No message to copy")
    
    def decode_message(self):
        """Decode the message from the video"""
        try:
            # Get values from UI
            method = self.method_combo.currentText()
            
            # Validate inputs
            if not self.input_video_path or not os.path.exists(self.input_video_path):
                ErrorHandler.show_error_message(
                    self.parent, "Invalid Input", 
                    "Please select a valid input video."
                )
                return
                
            # Clear previous message
            self.message_display.clear()
                
            # Start decoding thread
            self.progress_bar.setValue(0)
            self.decode_btn.setEnabled(False)
            
            # Create and start thread
            self.decode_thread = DecodeThread(
                method, self.input_video_path
            )
            self.decode_thread.progress.connect(self.update_progress)
            self.decode_thread.finished.connect(self.decoding_finished)
            self.decode_thread.start()
            
            # Update status
            self.parent.statusBar.showMessage("Decoding message...")
            
        except Exception as e:
            ErrorHandler.handle_error(self.parent, e, "Decoding Error")
            self.decode_btn.setEnabled(True)
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
    
    def decoding_finished(self, success, message):
        """Handle completion of decoding process"""
        self.decode_btn.setEnabled(True)
        
        if success:
            # Show the extracted message
            self.message_display.setText(message)
            self.parent.statusBar.showMessage("Message successfully decoded.")
        else:
            # Show error message
            ErrorHandler.show_warning_message(
                self.parent, "Decoding Failed", 
                f"Failed to decode message: {message}"
            )
            self.parent.statusBar.showMessage("Decoding failed.")
    
    def clear_form(self):
        """Clear all form inputs"""
        self.input_video_path = None
        self.video_path_edit.clear()
        self.message_display.clear()
        self.video_info_label.setText("No video selected")
        self.progress_bar.setValue(0)
        self.method_combo.setCurrentIndex(0)
        self.decode_btn.setEnabled(False)
        self.parent.statusBar.showMessage("Ready") 