import unittest
import os
import tempfile
import cv2
import numpy as np

from steganography import LSBSteganography

class TestLSBSteganography(unittest.TestCase):
    """Test cases for LSB steganography implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.steg = LSBSteganography()
        
        # Create a temporary video file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_video_path = os.path.join(self.temp_dir.name, "test_input.mp4")
        self.output_video_path = os.path.join(self.temp_dir.name, "test_output.mp4")
        
        # Create a simple test video (black frames)
        width, height = 320, 240
        fps = 30
        seconds = 1
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.input_video_path, fourcc, fps, (width, height))
        
        # Write black frames
        for _ in range(fps * seconds):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            out.write(frame)
        
        out.release()
        
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_text_to_binary(self):
        """Test conversion from text to binary"""
        text = "Hello"
        binary = self.steg.text_to_binary(text)
        self.assertEqual(len(binary), 40)  # 5 chars * 8 bits
        self.assertTrue(all(bit in '01' for bit in binary))
    
    def test_binary_to_text(self):
        """Test conversion from binary to text"""
        binary = '0100100001100101011011000110110001101111'  # "Hello"
        text = self.steg.binary_to_text(binary)
        self.assertEqual(text, "Hello")
    
    def test_hide_and_extract(self):
        """Test hiding and extracting message"""
        message = "This is a secret message"
        
        # Hide the message
        result = self.steg.hide_data(
            self.input_video_path,
            self.output_video_path,
            message
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_video_path))
        
        # Extract the message
        extracted = self.steg.extract_data(self.output_video_path)
        self.assertEqual(extracted, message)

if __name__ == '__main__':
    unittest.main() 