import cv2
import os
import numpy as np
from pathlib import Path

class VideoHandler:
    """
    Utility class for video processing operations
    """
    
    @staticmethod
    def get_video_info(video_path):
        """
        Get basic information about a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            dict: Dictionary with video information
        """
        if not os.path.exists(video_path):
            return {"error": "Video file not found"}
            
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"error": "Could not open video file"}
                
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Get file size
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Get file extension
            file_extension = os.path.splitext(video_path)[1]
            
            # Release resources
            cap.release()
            
            return {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "duration": duration,
                "file_size": file_size,
                "file_size_mb": file_size_mb,
                "file_extension": file_extension,
                "file_name": os.path.basename(video_path)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def validate_video(video_path):
        """
        Validate if a file is a valid video
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not os.path.exists(video_path):
            return False
            
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
                
            # Try to read the first frame
            ret, _ = cap.read()
            
            # Release resources
            cap.release()
            
            return ret
        except:
            return False
    
    @staticmethod
    def calculate_capacity(video_path, method="lsb"):
        """
        Calculate maximum data capacity for a video
        
        Args:
            video_path (str): Path to the video file
            method (str): Steganography method ('lsb' or 'dct')
            
        Returns:
            int: Maximum data capacity in bytes
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 0
                
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Release resources
            cap.release()
            
            # Calculate capacity based on method
            if method.lower() == "lsb":
                # For LSB, each pixel can store 3 bits (RGB channels)
                # We divide by 8 to convert to bytes
                return (width * height * 3 * frame_count) // 8
            elif method.lower() == "dct":
                # For DCT, each 8x8 block can store 1 bit
                # We divide by 8 to convert to bytes
                return ((width // 8) * (height // 8) * frame_count) // 8
            else:
                return 0
        except:
            return 0
    
    @staticmethod
    def extract_frame(video_path, frame_number=0):
        """
        Extract a specific frame from a video
        
        Args:
            video_path (str): Path to the video file
            frame_number (int): Frame number to extract
            
        Returns:
            numpy.ndarray: Extracted frame or None if failed
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
                
            # Set position to the requested frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            ret, frame = cap.read()
            
            # Release resources
            cap.release()
            
            if ret:
                return frame
            else:
                return None
        except:
            return None
    
    @staticmethod
    def save_output_path(input_path, suffix="_steg"):
        """
        Generate an output path for a processed video
        
        Args:
            input_path (str): Path to the input video
            suffix (str): Suffix to add to the filename
            
        Returns:
            str: Output path
        """
        path = Path(input_path)
        directory = path.parent
        filename = path.stem + suffix + path.suffix
        return str(directory / filename) 