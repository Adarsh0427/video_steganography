import cv2
import os
import numpy as np
from pathlib import Path
import subprocess

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
    def calculate_capacity(video_path, method):
        """
        Calculate the capacity of a video for steganography
        
        Args:
            video_path (str): Path to the video file
            method (str): Steganography method (LSB, DCT, or VIV)
            
        Returns:
            int: Capacity in bytes
        """
        try:
            # Get video info
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 0
                
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            cap.release()
            
            if method.lower() == "lsb":
                # Each pixel can store 1 bit in each color channel (RGB)
                # So each pixel can store 3 bits
                bits_per_frame = width * height * 3
                total_bits = bits_per_frame * frame_count
                return total_bits // 8  # Convert bits to bytes
                
            elif method.lower() == "dct":
                # Each 8x8 block can store 1 bit
                blocks_per_frame = (width // 8) * (height // 8)
                total_bits = blocks_per_frame * frame_count
                return total_bits // 8  # Convert bits to bytes
                
            elif method.lower() == "viv":
                # For video-in-video, we can store 2 bits per pixel (across all channels)
                # We use 2 frames to store 1 frame of secret video
                bits_per_frame = width * height * 2  # 2 bits per pixel
                total_bits = bits_per_frame * (frame_count // 2)  # Half the frames due to 2:1 ratio
                return total_bits // 8  # Convert bits to bytes
                
            else:
                raise ValueError(f"Unknown steganography method: {method}")
                
        except Exception as e:
            print(f"Error calculating capacity: {str(e)}")
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
    
    @staticmethod
    def recunstruct_video_from_frames(frames_folder, output_video_path, fps=30):
        """
        Reconstruct a video from a sequence of frames
        
        Args:
            frames_folder (str): Path to the input frames folder
            output_video_path (str): Path to save the output video
            fps (int): Frames per second for the output video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use FFmpeg for lossless encoding (H.265)
            ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite if exists
            "-framerate", str(fps),
            "-i", os.path.join(frames_folder, "%06d.png"),  # Frame sequence input
            "-c:v", "libx265",  # Use H.265
            "-preset", "medium",  # Balance between speed and compression
            "-x265-params", "lossless=1",  # Ensure lossless mode
            output_video_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True)
            
            for file in os.listdir(frames_folder):
                os.remove(os.path.join(frames_folder, file))
            os.rmdir(frames_folder)
            
            return True, "Data hidden successfully"
            
        except Exception as e:
            print(f"Error embedding frame: {str(e)}")
            return False, str(e)
