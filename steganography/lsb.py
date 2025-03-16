import cv2
import numpy as np
import bitarray
import base64
import os
import subprocess
from utils.video_handler import VideoHandler

class LSBSteganography:
    """
    Class for hiding and extracting data using the Least Significant Bit (LSB) steganography method.
    This method works by replacing the least significant bit of each color channel in video frames.
    """

    @staticmethod
    def text_to_binary(text):
        """
        Convert text to binary representation
        
        Args:
            text (str): Input text
        
        Returns:
            list: Binary representation of the text
        """
        bytes_message = text.encode('utf-8')
        encoded_message = base64.b64encode(bytes_message).decode('utf-8')
        ba = bitarray.bitarray()
        ba.frombytes(encoded_message.encode('utf-8'))

        # Convert to a bit array
        bit_array = [int(i) for i in ba]
        bit_array_length = len(bit_array)
        

        # Convert the length of the bit array into binary (e.g., use 16 bits)
        length_bits = list(map(int, bin(bit_array_length)[2:].zfill(16)))

        # Append length bits at the start of the message
        bit_array = length_bits + bit_array
        return bit_array

    @staticmethod
    def binary_to_text(binary_data):
        """
        Convert binary representation to text
        
        Args:
            binary_data (list): Binary data
            
        Returns:
            str: Decoded text
        """
        # Extract the length from first 16 bits
        length = int(''.join(map(str, binary_data[:16])), 2)

        # Get the actual message bits
        message_bits = binary_data[16:16+length]

        # Convert bits to bitarray
        ba = bitarray.bitarray(message_bits)

        # Convert to bytes and decode base64
        encoded_message = ba.tobytes().decode('utf-8')
        decoded_bytes = base64.b64decode(encoded_message)

        # Convert bytes to final text
        return decoded_bytes.decode('utf-8')
    
    @staticmethod
    def embed_data_into_frame(frame, bit_array):
        """ 
        Embed encoded data into the least significant bits of a video frame 
        Args:
            frame (numpy.ndarray): Video frame
            bit_array (list): Encoded data in binary format
            
        Returns:
            numpy.ndarray: Video frame with embedded data
        """
        data_index = 0
        rows, cols , _ = frame.shape

        for i in range(rows):
            for j in range(cols):
                # pixel = frame[i,j]
                for color in range(3):
                    if(data_index < len(bit_array)):
                        frame[i, j, color] = (frame[i, j, color] & 0b11111110) | (bit_array[data_index] & 1)
                        data_index+=1
                    else :
                        break

        return frame
    
    @staticmethod
    def extract_data_from_frame(frame):
        """
        Extract data from the least significant bits of a video frame
        
        Args:
            frame (numpy.ndarray): Video frame
            
        Returns:
            list: Extracted data in binary format
        """
        bit_array = []
        rows, cols, _ = frame.shape

        for i in range(rows):
            for j in range(cols):
                for color in range(3):
                    bit_array.append(frame[i, j, color] & 1)

        return bit_array

    def hide_data(self, video_path, output_path, secret_data):
        """
        Hide data within the first frame of a video file using LSB steganography. Embeds the data into the least significant bits of the first frame.

        Args:
            video_path (str): Path to the input video
            output_path (str): Path for the output video with hidden data
            secret_data (str): The secret message to hide

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            bit_array = self.text_to_binary(secret_data)

            first_frame = VideoHandler.extract_frame(video_path, 0)

            embeded_frame = self.embed_data_into_frame(first_frame, bit_array)

            VideoHandler.embed_frame_into_video(embeded_frame, video_path, output_path, 0)
            
            return True

        except Exception as e:
            print(f"Error hiding data: {e}")
            return False, "Error hiding data"

    def extract_data(self, video_path):
        """
        Extract hidden data from the first frame of a video file

        Args:
            video_path (str): Path to the video with hidden data

        Returns:
            str: Extracted message or error message
        """
        try:
            first_frame = VideoHandler.extract_frame(video_path, 0)
            bit_array = self.extract_data_from_frame(first_frame)

            message = self.binary_to_text(bit_array)
            
            return message

        except Exception as e:
            print(f"Error extracting data: {e}")
            return "Error extracting data"