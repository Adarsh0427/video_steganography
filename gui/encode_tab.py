import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QProgressBar,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIntValidator

from steganography import LSBSteganography, DCTSteganography
from utils.video_handler import VideoHandler
from utils.error_handling import ErrorHandler

class EncodeThread(QThread):
    """Thread for encoding messages to avoid UI freezing"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    
    def __init__(self, method, video_path, output_path, message):
        super().__init__()
        self.method = method
        self.video_path = video_path
        self.output_path = output_path
        self.message = message
    
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
            self.progress.emit(30)
                
            # Encode the message
            result = steg.hide_data(
                self.video_path,
                self.output_path,
                self.message,
            )
            
            # Update progress
            self.progress.emit(100)
            
            # Emit result
            if result:
                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, "Failed to encode message")
        
        except Exception as e:
            self.finished.emit(False, str(e))

class EncodeTab(QWidget):
    """Tab for encoding secret messages into videos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.input_video_path = None
        self.output_video_path = None
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
        self.video_path_edit.setPlaceholderText("Select input video file...")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_video)
        
        input_layout.addWidget(self.video_path_edit)
        input_layout.addWidget(browse_btn)
        
        # Video info display
        info_layout = QFormLayout()
        self.video_info_label = QLabel("No video selected")
        self.video_info_label.setWordWrap(True)
        self.capacity_label = QLabel("Available capacity: 0 bytes")
        
        info_layout.addRow("Video Details:", self.video_info_label)
        info_layout.addRow("Capacity:", self.capacity_label)
        
        video_layout.addLayout(input_layout)
        video_layout.addLayout(info_layout)
        video_group.setLayout(video_layout)
        
        # Message input section
        message_group = QGroupBox("Secret Message")
        message_layout = QVBoxLayout()
        
        # Message text area
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter your secret message here...")
        self.message_edit.textChanged.connect(self.update_message_stats)
        
        # Message stats
        stats_layout = QHBoxLayout()
        self.message_length_label = QLabel("Characters: 0")
        self.message_bytes_label = QLabel("Bytes: 0")
        
        stats_layout.addWidget(self.message_length_label)
        stats_layout.addWidget(self.message_bytes_label)
        
        message_layout.addWidget(self.message_edit)
        message_layout.addLayout(stats_layout)
        message_group.setLayout(message_layout)
        
        # Encoding options section
        options_group = QGroupBox("Encoding Options")
        options_layout = QFormLayout()
        
        # Steganography method
        self.method_combo = QComboBox()
        self.method_combo.addItems(["LSB", "DCT"])
        self.method_combo.currentTextChanged.connect(self.update_capacity)
        
        # Output file options
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("Output video will be saved here...")
        
        output_browse_btn = QPushButton("Browse")
        output_browse_btn.clicked.connect(self.browse_output)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(output_browse_btn)
        
        options_layout.addRow("Steganography Method:", self.method_combo)
        options_layout.addRow("Output Video:", output_layout)
        
        options_group.setLayout(options_layout)
        
        # Progress section
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.encode_btn = QPushButton("Encode Message")
        self.encode_btn.setEnabled(False)
        self.encode_btn.clicked.connect(self.encode_message)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.encode_btn)
        button_layout.addWidget(clear_btn)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(button_layout)
        
        # Add all components to main layout
        main_layout.addWidget(video_group)
        main_layout.addWidget(message_group)
        main_layout.addWidget(options_group)
        main_layout.addLayout(progress_layout)
        
        self.setLayout(main_layout)
    
    def browse_video(self):
        """Browse for input video file"""
        try:
            file_filter = "Video files (*.mp4 *.avi *.mov *.mkv);;All files (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Input Video", "", file_filter
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
        
        # Generate default output path
        self.output_video_path = VideoHandler.save_output_path(file_path)
        self.output_path_edit.setText(self.output_video_path)
        
        # Display video info
        self.display_video_info()
        
        # Update capacity
        self.update_capacity()
        
        # Check encode button state
        self.check_encode_button()
    
    def browse_output(self):
        """Browse for output video file location"""
        try:
            if not self.input_video_path:
                ErrorHandler.show_warning_message(
                    self.parent, "No Input Video", 
                    "Please select an input video file first."
                )
                return
                
            file_filter = "Video files (*.mp4);;All files (*.*)"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Output Video", self.output_video_path, file_filter
            )
            
            if file_path:
                self.output_video_path = file_path
                self.output_path_edit.setText(file_path)
                self.check_encode_button()
        except Exception as e:
            ErrorHandler.handle_error(self.parent, e, "Output Selection Error")
    
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
    
    def update_capacity(self):
        """Update the capacity information based on the video and method"""
        if not self.input_video_path:
            return
            
        try:
            method = self.method_combo.currentText().lower()
            capacity = VideoHandler.calculate_capacity(self.input_video_path, method)
            
            if capacity > 1024 * 1024:
                capacity_text = f"{capacity / (1024 * 1024):.2f} MB"
            elif capacity > 1024:
                capacity_text = f"{capacity / 1024:.2f} KB"
            else:
                capacity_text = f"{capacity} bytes"
                
            self.capacity_label.setText(f"Available capacity: {capacity_text}")
            
            # Check if message fits
            message_bytes = len(self.message_edit.toPlainText().encode('utf-8'))
            if message_bytes > capacity:
                self.capacity_label.setStyleSheet("color: red;")
            else:
                self.capacity_label.setStyleSheet("")
                
            # Update encode button state
            self.check_encode_button()
            
        except Exception as e:
            ErrorHandler.log_exception(e, "Error calculating capacity")
            self.capacity_label.setText("Error calculating capacity")
    
    def update_message_stats(self):
        """Update message statistics"""
        text = self.message_edit.toPlainText()
        char_count = len(text)
        byte_count = len(text.encode('utf-8'))
        
        self.message_length_label.setText(f"Characters: {char_count}")
        self.message_bytes_label.setText(f"Bytes: {byte_count}")
        
        # Update capacity color if needed
        self.update_capacity()
        
        # Check encode button state
        self.check_encode_button()
    
    def check_encode_button(self):
        """Check if encode button should be enabled"""
        enable = False
        
        if (self.input_video_path and 
            self.message_edit.toPlainText() and 
            self.output_video_path):
            
            method = self.method_combo.currentText().lower()
            capacity = VideoHandler.calculate_capacity(self.input_video_path, method)
            message_bytes = len(self.message_edit.toPlainText().encode('utf-8'))
            
            if message_bytes <= capacity:
                enable = True
        
        self.encode_btn.setEnabled(enable)
    
    def encode_message(self):
        """Encode the message into the video"""
        try:
            # Get values from UI
            message = self.message_edit.toPlainText()
            method = self.method_combo.currentText()
            
            # Validate inputs
            if not message:
                ErrorHandler.show_error_message(
                    self.parent, "No Message", 
                    "Please enter a message to hide."
                )
                return
                
            if not self.input_video_path or not os.path.exists(self.input_video_path):
                ErrorHandler.show_error_message(
                    self.parent, "Invalid Input", 
                    "Please select a valid input video."
                )
                return
                
            if not self.output_video_path:
                ErrorHandler.show_error_message(
                    self.parent, "No Output Path", 
                    "Please specify an output video path."
                )
                return
                
            # Start encoding thread
            self.progress_bar.setValue(0)
            self.encode_btn.setEnabled(False)
            
            # Create and start thread
            self.encode_thread = EncodeThread(
                method, self.input_video_path, self.output_video_path, 
                message
            )
            self.encode_thread.progress.connect(self.update_progress)
            self.encode_thread.finished.connect(self.encoding_finished)
            self.encode_thread.start()
            
            # Update status
            self.parent.statusBar.showMessage("Encoding message...")
            
        except Exception as e:
            ErrorHandler.handle_error(self.parent, e, "Encoding Error")
            self.encode_btn.setEnabled(True)
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
    
    def encoding_finished(self, success, message):
        """Handle completion of encoding process"""
        self.encode_btn.setEnabled(True)
        
        if success:
            # Show success message
            ErrorHandler.show_info_message(
                self.parent, "Success", 
                f"Message successfully encoded in the video.\n\nSaved to: {message}"
            )
            self.parent.statusBar.showMessage("Encoding completed successfully.")
        else:
            # Show error message
            ErrorHandler.show_error_message(
                self.parent, "Encoding Failed", 
                f"Failed to encode message: {message}"
            )
            self.parent.statusBar.showMessage("Encoding failed.")
    
    def clear_form(self):
        """Clear all form inputs"""
        self.input_video_path = None
        self.output_video_path = None
        self.video_path_edit.clear()
        self.output_path_edit.clear()
        self.message_edit.clear()
        self.video_info_label.setText("No video selected")
        self.capacity_label.setText("Available capacity: 0 bytes")
        self.progress_bar.setValue(0)
        self.method_combo.setCurrentIndex(0)
        self.encode_btn.setEnabled(False)
        self.parent.statusBar.showMessage("Ready") 