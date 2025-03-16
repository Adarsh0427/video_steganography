import unittest
import os
import tempfile
import cv2
import numpy as np

from steganography import DCTSteganography

class TestDCTSteganography(unittest.TestCase):
    """Test cases for DCT steganography implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.steg = DCTSteganography()
        
        # Create a temporary video file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_video_path = os.path.join(self.temp_dir.name, "test_input.mp4")
        self.output_video_path = os.path.join(self.temp_dir.name, "test_output.mp4")
        
        # Create a simple test video (gray frames - better for DCT)
        width, height = 320, 240
        fps = 30
        seconds = 1
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.input_video_path, fourcc, fps, (width, height))
        
        # Write gray frames
        for _ in range(fps * seconds):
            # Gray frame (value 128) works better for DCT
            frame = np.ones((height, width, 3), dtype=np.uint8) * 128
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
    
    def test_dct_and_idct(self):
        """Test DCT and inverse DCT operations"""
        # Create a simple 8x8 block
        block = np.ones((8, 8), dtype=float) * 128
        
        # Apply DCT
        dct_block = self.steg.dct_block(block)
        
        # Apply inverse DCT
        idct_block = self.steg.idct_block(dct_block)
        
        # Check if the block is approximately the same
        np.testing.assert_allclose(block, idct_block, rtol=1e-5, atol=1)
    
    def test_embed_and_extract_bit(self):
        """Test embedding and extracting a bit"""
        # Create a simple 8x8 block
        block = np.ones((8, 8), dtype=float) * 128
        
        # Apply DCT
        dct_block = self.steg.dct_block(block)
        
        # Embed bit 1
        modified_block = self.steg.embed_bit(dct_block.copy(), 1)
        extracted_bit = self.steg.extract_bit(modified_block)
        self.assertEqual(extracted_bit, 1)
        
        # Embed bit 0
        modified_block = self.steg.embed_bit(dct_block.copy(), 0)
        extracted_bit = self.steg.extract_bit(modified_block)
        self.assertEqual(extracted_bit, 0)
    
    def test_hide_and_extract(self):
        """Test hiding and extracting message"""
        message = "This is a short secret message"  # Shortened to fit in first frame
        
        # Hide the message
        result = self.steg.hide_data(
            self.input_video_path,
            self.output_video_path,
            message,
            None  # No password
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_video_path))
        
        # Extract the message
        extracted = self.steg.extract_data(self.output_video_path, None)
        self.assertEqual(extracted, message)

if __name__ == '__main__':
    unittest.main() 