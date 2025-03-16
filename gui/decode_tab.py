import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QProgressBar,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QRadioButton, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QApplication

from steganography import LSBSteganography, VideoInVideoSteganography
from utils.video_handler import VideoHandler
from utils.error_handling import ErrorHandler

class DecodeThread(QThread):
    """Thread for decoding messages to avoid UI freezing"""
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, method, video_path, output_path=None):
        super().__init__()
        self.method = method
        self.video_path = video_path
        self.output_path = output_path
        
    def run(self):
        try:
            # Initial progress
            self.progress_updated.emit(10)
            
            if self.method == "LSB":
                steg = LSBSteganography()
                # Start processing
                self.progress_updated.emit(30)
                message = steg.extract_data(self.video_path)
                # Almost done
                self.progress_updated.emit(90)
                self.finished.emit(True, message)
            elif self.method == "VIV":
                steg = VideoInVideoSteganography()
                # Start processing
                self.progress_updated.emit(30)
                success = steg.extract_video(self.video_path, self.output_path)
                # Almost done
                self.progress_updated.emit(90)
                self.finished.emit(success, "" if success else "Failed to extract video")
            
            # Final progress
            self.progress_updated.emit(100)
                
        except Exception as e:
            self.progress_updated.emit(0)
            self.finished.emit(False, str(e))

class DecodeTab(QWidget):
    """Tab for decoding secret messages from videos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.steg = None
        self.method = "LSB"  # Default method
        self.video_path = ""
        self.output_path = ""  # For video-in-video
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        # Main layout
        layout = QVBoxLayout()
        
        # Method selection
        method_group = QGroupBox("Steganography Method")
        method_layout = QHBoxLayout()
        
        self.lsb_radio = QRadioButton("LSB")
        self.viv_radio = QRadioButton("Video-in-Video")
        
        self.lsb_radio.setChecked(True)
        method_layout.addWidget(self.lsb_radio)
        method_layout.addWidget(self.viv_radio)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Connect radio buttons
        self.lsb_radio.toggled.connect(self.method_changed)
        self.viv_radio.toggled.connect(self.method_changed)
        
        # Input video selection
        input_group = QGroupBox("Input")
        input_layout = QHBoxLayout()
        
        self.video_label = QLabel("Stego Video:")
        self.video_path_input = QLineEdit()
        self.video_path_input.setReadOnly(True)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_video)
        
        input_layout.addWidget(self.video_label)
        input_layout.addWidget(self.video_path_input)
        input_layout.addWidget(self.browse_button)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section (changes based on method)
        self.output_stack = QStackedWidget()
        
        # Message output for LSB
        message_widget = QWidget()
        message_layout = QVBoxLayout()
        message_layout.addWidget(QLabel("Extracted Message:"))
        
        # Message output with copy button
        message_output_layout = QHBoxLayout()
        self.message_output = QTextEdit()
        self.message_output.setReadOnly(True)
        message_output_layout.addWidget(self.message_output)
        
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy_message)
        message_output_layout.addWidget(copy_button)
        
        message_layout.addLayout(message_output_layout)
        message_widget.setLayout(message_layout)
        
        # Video output for Video-in-Video
        video_output_widget = QWidget()
        video_output_layout = QHBoxLayout()
        video_output_layout.addWidget(QLabel("Output Video:"))
        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_browse = QPushButton("Browse")
        self.output_browse.clicked.connect(self.browse_output)
        
        video_output_layout.addWidget(self.output_path_input)
        video_output_layout.addWidget(self.output_browse)
        video_output_widget.setLayout(video_output_layout)
        
        self.output_stack.addWidget(message_widget)  # Index 0: Message output
        self.output_stack.addWidget(video_output_widget)  # Index 1: Video output
        
        layout.addWidget(self.output_stack)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Decode button
        self.decode_button = QPushButton("Decode")
        self.decode_button.clicked.connect(self.start_decoding)
        self.decode_button.setEnabled(False)
        layout.addWidget(self.decode_button)
        
        self.setLayout(layout)
    
    def copy_message(self):
        """Copy extracted message to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.message_output.toPlainText())
        self.status_label.setText("Message copied to clipboard!")
    
    def method_changed(self):
        """Handle steganography method change"""
        if self.lsb_radio.isChecked():
            self.method = "LSB"
            self.output_stack.setCurrentIndex(0)  # Show message output
        else:  # Video-in-Video
            self.method = "VIV"
            self.output_stack.setCurrentIndex(1)  # Show video output
            self.update_output_path()
        
        # Clear output when method changes
        if self.method == "LSB":
            self.message_output.clear()
        else:
            self.output_path_input.clear()
            self.output_path = ""
        
        self.check_decode_button()
    
    def browse_video(self):
        """Browse for input video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Stego Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        if file_path:
            if VideoHandler.validate_video(file_path):
                self.video_path = file_path
                self.video_path_input.setText(file_path)
                self.update_output_path()
                self.check_decode_button()
            else:
                QMessageBox.warning(self, "Error", "Selected file is not a valid video.")
    
    def browse_output(self):
        """Browse for output video path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        if file_path:
            self.output_path = file_path
            self.output_path_input.setText(file_path)
            self.check_decode_button()
    
    def update_output_path(self):
        """Update default output path based on input"""
        if not self.video_path:
            return
            
        if self.method == "VIV":
            base_path = os.path.splitext(self.video_path)[0]
            self.output_path = f"{base_path}_extracted.mp4"
            self.output_path_input.setText(self.output_path)
    
    def check_decode_button(self):
        """Enable decode button if inputs are valid"""
        if not self.video_path:
            self.decode_button.setEnabled(False)
            return
            
        if self.method == "VIV" and not self.output_path:
            self.decode_button.setEnabled(False)
            return
            
        self.decode_button.setEnabled(True)
    
    def start_decoding(self):
        """Start the decoding process"""
        self.decode_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Decoding...")
        
        if self.method == "VIV":
            self.steg = VideoInVideoSteganography()
            self.decode_thread = DecodeThread(
                method=self.method,
                video_path=self.video_path,
                output_path=self.output_path
            )
        else:
            self.steg = LSBSteganography()
            self.decode_thread = DecodeThread(
                method=self.method,
                video_path=self.video_path
            )
        
        self.decode_thread.progress_updated.connect(self.update_progress)
        self.decode_thread.finished.connect(self.decoding_finished)
        self.decode_thread.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def decoding_finished(self, success, result):
        """Handle completion of decoding process"""
        self.decode_button.setEnabled(True)
        
        if success:
            if self.method == "VIV":
                self.status_label.setText("Video extracted successfully!")
                QMessageBox.information(self, "Success", "Secret video has been extracted successfully.")
                # Clear form after successful extraction
                self.clear_form()
            else:
                self.message_output.setText(result)
                self.status_label.setText("Message extracted successfully!")
                # Don't clear immediately for LSB so user can see the message
        else:
            self.status_label.setText("Decoding failed!")
            QMessageBox.warning(self, "Error", f"Failed to decode: {result}")
            # Reset progress bar
            self.progress_bar.setValue(0)

    def clear_form(self):
        """Clear all form inputs"""
        # Clear paths
        self.video_path = ""
        self.output_path = ""
        
        # Clear UI elements
        self.video_path_input.clear()
        self.output_path_input.clear()
        self.message_output.clear()
        
        # Reset labels
        self.video_label.setText("Stego Video:")
        self.status_label.setText("Ready")
        
        # Reset progress
        self.progress_bar.setValue(0)
        
        # Keep current method but reset its output view
        if self.method == "LSB":
            self.output_stack.setCurrentIndex(0)
        else:
            self.output_stack.setCurrentIndex(1)
        
        # Disable decode button
        self.decode_button.setEnabled(False)
        
        # Update status bar
        if self.parent:
            self.parent.statusBar.showMessage("Ready") 