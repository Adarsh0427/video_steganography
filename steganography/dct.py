import cv2
import numpy as np
from scipy.fftpack import dct, idct

class DCTSteganography:
    """
    Class for hiding and extracting data using Discrete Cosine Transform (DCT) steganography method.
    DCT is used in JPEG compression and can be used for robust steganography.
    """
    
    def __init__(self, quantization=50):
        """
        Initialize DCT steganography with quantization parameter
        
        Args:
            quantization (int): Quantization factor for DCT coefficients
        """
        self.quantization = quantization
    
    @staticmethod
    def text_to_binary(text):
        """Convert text to binary representation"""
        if type(text) == str:
            text = text.encode('utf-8')
        return ''.join(format(byte, '08b') for byte in text)
    
    @staticmethod
    def binary_to_text(binary):
        """Convert binary representation to text"""
        binary_values = [binary[i:i+8] for i in range(0, len(binary), 8)]
        byte_array = bytearray(int(binary_value, 2) for binary_value in binary_values)
        return byte_array.decode('utf-8', errors='ignore')
    
    def dct_block(self, block):
        """Apply DCT to an 8x8 block"""
        return dct(dct(block.T, norm='ortho').T, norm='ortho')
    
    def idct_block(self, block):
        """Apply inverse DCT to an 8x8 block"""
        return idct(idct(block.T, norm='ortho').T, norm='ortho')
    
    def embed_bit(self, dct_block, bit):
        """
        Embed a single bit into a DCT block
        
        Args:
            dct_block: 8x8 DCT block
            bit: 0 or 1 to embed
            
        Returns:
            Modified DCT block
        """
        # We'll use mid-frequency coefficients for embedding
        # Modify coefficient (4,5) based on bit value
        if bit == 1:
            if dct_block[4, 5] <= 0:
                dct_block[4, 5] = -self.quantization
        else:
            if dct_block[4, 5] > 0:
                dct_block[4, 5] = self.quantization
        
        return dct_block
    
    def extract_bit(self, dct_block):
        """
        Extract a single bit from a DCT block
        
        Args:
            dct_block: 8x8 DCT block
            
        Returns:
            Extracted bit (0 or 1)
        """
        return 1 if dct_block[4, 5] <= 0 else 0
    
    def hide_data(self, video_path, output_path, secret_data):
        """
        Hide data within a video file using DCT steganography.
        This implementation embeds the data only in the first frame for reliability.
        
        Args:
            video_path (str): Path to the input video
            output_path (str): Path for the output video with hidden data
            secret_data (str): The secret message to hide
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                print("Could not open video file")
                return False
                
            # Get video properties
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)
            
            # Convert message to binary
            binary_data = self.text_to_binary(str(len(secret_data)) + ":" + secret_data)
            data_len = len(binary_data)
            
            # Calculate maximum data capacity for first frame
            max_bits = (width // 8) * (height // 8)
            if data_len > max_bits:
                print(f"Message too large. Capacity: {max_bits} bits, Required: {data_len} bits")
                return False
            
            # Read first frame
            ret, frame = video.read()
            if not ret:
                print("Could not read first frame")
                return False
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Convert frame to grayscale for DCT processing
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Embed data in first frame
            data_index = 0
            for y in range(0, height - 8, 8):
                for x in range(0, width - 8, 8):
                    if data_index >= data_len:
                        break
                    
                    # Get 8x8 block
                    block = gray_frame[y:y+8, x:x+8].astype(float)
                    
                    # Apply DCT
                    dct_block = self.dct_block(block)
                    
                    # Embed bit
                    bit = int(binary_data[data_index])
                    dct_block = self.embed_bit(dct_block, bit)
                    data_index += 1
                    
                    # Apply inverse DCT
                    modified_block = self.idct_block(dct_block).astype(np.uint8)
                    
                    # Update all channels with the modified luminance
                    for c in range(3):  # Apply to all channels for better preservation
                        for i in range(8):
                            for j in range(8):
                                frame[y+i, x+j, c] = modified_block[i, j]
                
                if data_index >= data_len:
                    break
            
            # Write modified first frame
            out.write(frame)
            
            # Copy remaining frames
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                out.write(frame)
            
            # Release resources
            video.release()
            out.release()
            
            print(f"Successfully embedded {data_len} bits of data in the first frame")
            return True
            
        except Exception as e:
            print(f"Error hiding data: {str(e)}")
            return False
    
    def extract_data(self, video_path):
        """
        Extract hidden data from a video file.
        This implementation extracts data only from the first frame.
        
        Args:
            video_path (str): Path to the video with hidden data
            
        Returns:
            str: Extracted message
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                return "Could not open video file"
            
            # Read first frame
            ret, frame = video.read()
            if not ret:
                return "Could not read first frame"
            
            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = gray_frame.shape
            
            # Extract binary data
            binary_data = ""
            
            for y in range(0, height - 8, 8):
                for x in range(0, width - 8, 8):
                    # Get 8x8 block
                    block = gray_frame[y:y+8, x:x+8].astype(float)
                    
                    # Apply DCT
                    dct_block = self.dct_block(block)
                    
                    # Extract bit
                    bit = self.extract_bit(dct_block)
                    binary_data += str(bit)
                    
                    # Try to extract message length
                    if len(binary_data) % 8 == 0 and len(binary_data) >= 16:
                        # Convert binary to string to check for delimiter
                        try:
                            current_data = self.binary_to_text(binary_data)
                            
                            # Check if we have the delimiter for message length
                            if ":" in current_data:
                                # Split to get length and part of message
                                parts = current_data.split(":", 1)
                                
                                # Get message length
                                msg_length = int(parts[0])
                                
                                # Get total length needed in binary
                                total_length = len(self.text_to_binary(parts[0] + ":" + parts[1][:msg_length]))
                                
                                # If we have all the data needed
                                if len(binary_data) >= total_length:
                                    # Extract actual message
                                    full_message = self.binary_to_text(binary_data)
                                    message_parts = full_message.split(":", 1)
                                    
                                    # Return only the actual message, not its length
                                    if len(message_parts) > 1:
                                        return message_parts[1][:msg_length]
                        except Exception as e:
                            # Continue if we can't parse yet
                            pass
            
            # Release resources
            video.release()
            return "No hidden message found"
            
        except Exception as e:
            print(f"Error extracting data: {str(e)}")
            return f"Error extracting data: {str(e)}" 