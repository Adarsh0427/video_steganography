import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QProgressBar,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QFrame, QRadioButton, QStackedWidget,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIntValidator

from steganography import LSBSteganography, VideoInVideoSteganography
from utils.video_handler import VideoHandler
from utils.error_handling import ErrorHandler

class EncodeThread(QThread):
    """Thread for encoding messages to avoid UI freezing"""
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, method, video_path, output_path, message=None, secret_path=None):
        super().__init__()
        self.method = method
        self.video_path = video_path
        self.output_path = output_path
        self.message = message
        self.secret_path = secret_path
    
    def run(self):
        try:
            # Initial progress
            self.progress_updated.emit(10)
            
            if self.method == "LSB":
                steg = LSBSteganography()
                # Start processing
                self.progress_updated.emit(30)
                result = steg.hide_data(
                    self.video_path,
                    self.output_path,
                    self.message
                )
                # Almost done
                self.progress_updated.emit(90)
            elif self.method == "VIV":
                steg = VideoInVideoSteganography()
                # Start processing
                self.progress_updated.emit(30)
                result = steg.hide_video(
                    self.video_path,
                    self.secret_path,
                    self.output_path
                )
                # Almost done
                self.progress_updated.emit(90)
            
            # Final progress and result
            self.progress_updated.emit(100)
            if result:
                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, "Failed to encode")
        
        except Exception as e:
            self.progress_updated.emit(0)
            self.finished.emit(False, str(e))

class EncodeTab(QWidget):
    """Tab for encoding secret messages into videos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.input_video_path = None
        self.output_video_path = None
        self.steg = None
        self.method = "LSB"  # Default method
        self.video_path = ""
        self.secret_path = ""  # For video-in-video
        self.message = ""
        self.output_path = ""
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # Method selection
        method_group = QGroupBox("Steganography Method")
        method_layout = QHBoxLayout()
        
        self.lsb_radio = QRadioButton("LSB")
        self.viv_radio = QRadioButton("Video-in-Video")
        
        self.lsb_radio.setChecked(True)
        method_layout.addWidget(self.lsb_radio)
        method_layout.addWidget(self.viv_radio)
        
        method_group.setLayout(method_layout)
        main_layout.addWidget(method_group)
        
        # Connect radio buttons
        self.lsb_radio.toggled.connect(self.method_changed)
        self.viv_radio.toggled.connect(self.method_changed)
        
        # Input section
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        # Cover video selection
        cover_layout = QHBoxLayout()
        self.cover_label = QLabel("Cover Video:")
        self.cover_path = QLineEdit()
        self.cover_path.setReadOnly(True)
        self.cover_browse = QPushButton("Browse")
        self.cover_browse.clicked.connect(self.browse_video)
        
        cover_layout.addWidget(self.cover_label)
        cover_layout.addWidget(self.cover_path)
        cover_layout.addWidget(self.cover_browse)
        input_layout.addLayout(cover_layout)
        
        # Secret content section
        self.secret_stack = QStackedWidget()
        
        # Message input for LSB
        message_widget = QWidget()
        message_layout = QVBoxLayout()
        message_layout.addWidget(QLabel("Message:"))
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter your secret message here...")
        self.message_input.textChanged.connect(self.update_message_stats)
        message_layout.addWidget(self.message_input)
        message_widget.setLayout(message_layout)
        
        # Secret video input for Video-in-Video
        secret_video_widget = QWidget()
        secret_video_layout = QHBoxLayout()
        secret_video_layout.addWidget(QLabel("Secret Video:"))
        self.secret_video_path = QLineEdit()
        self.secret_video_path.setReadOnly(True)
        self.secret_video_browse = QPushButton("Browse")
        self.secret_video_browse.clicked.connect(self.browse_secret_video)
        
        secret_video_layout.addWidget(self.secret_video_path)
        secret_video_layout.addWidget(self.secret_video_browse)
        secret_video_widget.setLayout(secret_video_layout)
        
        self.secret_stack.addWidget(message_widget)  # Index 0: Message input
        self.secret_stack.addWidget(secret_video_widget)  # Index 1: Secret video input
        
        input_layout.addWidget(self.secret_stack)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()
        
        self.output_label = QLabel("Output Path:")
        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_browse = QPushButton("Browse")
        self.output_browse.clicked.connect(self.browse_output)
        
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path_input)
        output_layout.addWidget(self.output_browse)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Encode button
        self.encode_button = QPushButton("Encode")
        self.encode_button.clicked.connect(self.start_encoding)
        self.encode_button.setEnabled(False)
        main_layout.addWidget(self.encode_button)
        
        self.setLayout(main_layout)
    
    def method_changed(self):
        """Handle steganography method change"""
        if self.lsb_radio.isChecked():
            self.method = "LSB"
            self.secret_stack.setCurrentIndex(0)  # Show message input
        else:  # Video-in-Video
            self.method = "VIV"
            self.secret_stack.setCurrentIndex(1)  # Show secret video input
        
        # Clear output path when method changes
        self.output_path_input.clear()
        self.output_video_path = None
        self.check_encode_button()
    
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
        self.cover_path.setText(file_path)
        
        # Generate default output path
        self.output_video_path = VideoHandler.save_output_path(file_path)
        self.output_path_input.setText(self.output_video_path)
        
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
                self.output_path_input.setText(file_path)
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
                self.cover_label.setText(f"Error: {info['error']}")
                return
                
            # Format and display video information
            info_text = (
                f"Name: {info['file_name']}\n"
                f"Size: {info['file_size_mb']:.2f} MB\n"
                f"Resolution: {info['width']}x{info['height']}\n"
                f"Duration: {info['duration']:.2f} seconds\n"
                f"FPS: {info['fps']:.2f}"
            )
            
            self.cover_label.setText(info_text)
            
        except Exception as e:
            ErrorHandler.log_exception(e, "Error displaying video info")
            self.cover_label.setText("Error retrieving video information")
    
    def update_capacity(self):
        """Update the capacity information based on the video and method"""
        if not self.input_video_path:
            return
            
        try:
            method = self.method
            capacity = VideoHandler.calculate_capacity(self.input_video_path, method)
            
            if capacity > 1024 * 1024:
                capacity_text = f"{capacity / (1024 * 1024):.2f} MB"
            elif capacity > 1024:
                capacity_text = f"{capacity / 1024:.2f} KB"
            else:
                capacity_text = f"{capacity} bytes"
                
            self.output_label.setText(f"Available capacity: {capacity_text}")
            
            # Check if message fits
            message_bytes = len(self.message_input.toPlainText().encode('utf-8'))
            if message_bytes > capacity:
                self.output_label.setStyleSheet("color: red;")
            else:
                self.output_label.setStyleSheet("")
                
            # Update encode button state
            self.check_encode_button()
            
        except Exception as e:
            ErrorHandler.log_exception(e, "Error calculating capacity")
            self.output_label.setText("Error calculating capacity")
    
    def update_message_stats(self):
        """Update message statistics"""
        text = self.message_input.toPlainText()
        char_count = len(text)
        byte_count = len(text.encode('utf-8'))
        
        self.output_label.setText(f"Available capacity: {char_count} characters, {byte_count} bytes")
        
        # Update capacity color if needed
        self.update_capacity()
        
        # Check encode button state
        self.check_encode_button()
    
    def check_encode_button(self):
        """Check if encode button should be enabled"""
        enable = False
        
        if not self.input_video_path:
            return
            
        if self.method == "VIV":
            # For video-in-video, check if both videos are selected
            if self.secret_path and self.output_video_path:
                # Check if secret video is shorter than cover video
                cover_info = VideoHandler.get_video_info(self.input_video_path)
                secret_info = VideoHandler.get_video_info(self.secret_path)
                
                if cover_info and secret_info:
                    cover_frames = cover_info.get('frame_count', 0)
                    secret_frames = secret_info.get('frame_count', 0)
                    
                    # Secret video should be less than half the length of cover video
                    # since we use 2 cover frames to store 1 secret frame
                    if secret_frames <= (cover_frames // 2):
                        enable = True
                    else:
                        self.status_label.setText("Secret video is too long for the cover video")
        else:
            # For LSB, check message size against capacity
            if self.message_input.toPlainText() and self.output_video_path:
                capacity = VideoHandler.calculate_capacity(self.input_video_path, self.method)
                message_bytes = len(self.message_input.toPlainText().encode('utf-8'))
                
                if message_bytes <= capacity:
                    enable = True
                else:
                    self.status_label.setText("Message is too large for the selected video")
        
        self.encode_button.setEnabled(enable)
    
    def start_encoding(self):
        """Start the encoding process"""
        if not self.validate_inputs():
            return
            
        self.encode_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Encoding...")
        
        if self.method == "VIV":
            self.steg = VideoInVideoSteganography()
            self.encode_thread = EncodeThread(
                method=self.method,
                video_path=self.input_video_path,
                secret_path=self.secret_video_path.text(),
                output_path=self.output_video_path
            )
        else:
            self.steg = LSBSteganography()
            
            self.message = self.message_input.toPlainText()
            self.encode_thread = EncodeThread(
                method=self.method,
                video_path=self.input_video_path,
                output_path=self.output_video_path,
                message=self.message
            )
        
        self.encode_thread.progress_updated.connect(self.update_progress)
        self.encode_thread.finished.connect(self.encoding_finished)
        self.encode_thread.start()
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
    
    def encoding_finished(self, success, message):
        """Handle completion of encoding process"""
        self.encode_button.setEnabled(True)
        
        if success:
            # Show success message
            ErrorHandler.show_info_message(
                self.parent, "Success", 
                f"Message successfully encoded in the video.\n\nSaved to: {message}"
            )
            self.parent.statusBar.showMessage("Encoding completed successfully.")
            
            # Clear all fields after successful encoding
            self.clear_form()
        else:
            # Show error message
            ErrorHandler.show_error_message(
                self.parent, "Encoding Failed", 
                f"Failed to encode message: {message}"
            )
            self.parent.statusBar.showMessage("Encoding failed.")
            
            # Reset progress bar and status
            self.progress_bar.setValue(0)
            self.status_label.setText("Ready")
    
    def browse_secret_video(self):
        """Browse for secret video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Secret Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        if file_path:
            self.secret_path = file_path
            self.secret_video_path.setText(file_path)
            self.update_output_path()

    def update_output_path(self):
        """Update default output path based on input"""
        if not self.input_video_path:
            return
            
        base_path = os.path.splitext(self.input_video_path)[0]
        if self.method == "VIV":
            self.output_video_path = f"{base_path}_stego.mkv"
        else:
            self.output_video_path = f"{base_path}_stego.mp4"
        self.output_path_input.setText(self.output_video_path)

    def validate_inputs(self):
        """Validate user inputs before encoding"""
        if not self.input_video_path:
            QMessageBox.warning(self, "Error", "Please select a cover video.")
            return False
            
        if self.method == "VIV":
            if not self.secret_path:
                QMessageBox.warning(self, "Error", "Please select a secret video.")
                return False
        else:
            if not self.message_input.toPlainText().strip():
                QMessageBox.warning(self, "Error", "Please enter a message.")
                return False
                
        if not self.output_video_path:
            QMessageBox.warning(self, "Error", "Please select an output path.")
            return False
            
        return True

    def clear_form(self):
        """Clear all form inputs"""
        # Clear paths
        self.input_video_path = None
        self.output_video_path = None
        self.secret_path = ""
        
        # Clear UI elements
        self.cover_path.clear()
        self.output_path_input.clear()
        self.message_input.clear()
        self.secret_video_path.clear()
        
        # Reset labels
        self.cover_label.setText("Cover Video:")
        self.output_label.setText("Output Path:")
        self.status_label.setText("Ready")
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Keep current method but reset its input
        if self.method == "LSB":
            self.secret_stack.setCurrentIndex(0)
        else:
            self.secret_stack.setCurrentIndex(1)
        
        # Disable encode button
        self.encode_button.setEnabled(False)
        
        # Update status bar
        if self.parent:
            self.parent.statusBar.showMessage("Ready") 