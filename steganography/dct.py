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
    
    def hide_data(self, video_path, output_path, secret_data, password=None):
        """
        Hide data within a video file using DCT steganography
        
        Args:
            video_path (str): Path to the input video
            output_path (str): Path for the output video with hidden data
            secret_data (str): The secret message to hide
            password (str, optional): Password to encrypt data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                return False
                
            # Get video properties
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Add header to know the length of the message
            binary_data = self.text_to_binary(str(len(secret_data)) + ":" + secret_data)
            data_len = len(binary_data)
            
            # Calculate maximum data capacity
            # Each 8x8 block can store 1 bit
            max_bits = (width // 8) * (height // 8) * frame_count
            if data_len > max_bits:
                return False
            
            data_index = 0
            complete = False
            
            # Process each frame
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                # Convert frame to grayscale for DCT processing
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # If we still have data to hide
                if not complete:
                    # Process 8x8 blocks
                    for y in range(0, height - 8, 8):
                        for x in range(0, width - 8, 8):
                            # Skip if we've embedded all data
                            if data_index >= data_len:
                                complete = True
                                break
                            
                            # Get 8x8 block
                            block = gray_frame[y:y+8, x:x+8].astype(float)
                            
                            # Apply DCT
                            dct_block = self.dct_block(block)
                            
                            # Embed bit and apply inverse DCT
                            if data_index < data_len:
                                bit = int(binary_data[data_index])
                                dct_block = self.embed_bit(dct_block, bit)
                                data_index += 1
                            
                            # Apply inverse DCT
                            modified_block = self.idct_block(dct_block).astype(np.uint8)
                            
                            # Update frame with modified block
                            # We only modify the Y channel in YUV color space
                            for i in range(8):
                                for j in range(8):
                                    frame[y+i, x+j, 0] = modified_block[i, j]
                        
                        if complete:
                            break
                
                # Write the frame
                out.write(frame)
            
            # Release resources
            video.release()
            out.release()
            
            return True
        except Exception as e:
            print(f"Error hiding data: {e}")
            return False
    
    def extract_data(self, video_path, password=None):
        """
        Extract hidden data from a video file
        
        Args:
            video_path (str): Path to the video with hidden data
            password (str, optional): Password to decrypt data
            
        Returns:
            str: Extracted message
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            binary_data = ""
            
            # Read all frames
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                
                # Convert frame to grayscale
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                height, width = gray_frame.shape
                
                # Process 8x8 blocks
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
                        if len(binary_data) % 8 == 0:
                            # Convert binary to string to check for delimiter
                            current_data = self.binary_to_text(binary_data)
                            
                            # Check if we have the delimiter for message length
                            if ":" in current_data:
                                # Split to get length and part of message
                                parts = current_data.split(":", 1)
                                
                                try:
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
                                        return message_parts[1][:msg_length]
                                except:
                                    # Continue if we can't parse the length yet
                                    pass
            
            # Release resources
            video.release()
            return "No hidden message found"
        except Exception as e:
            print(f"Error extracting data: {e}")
            return "Error extracting data" 