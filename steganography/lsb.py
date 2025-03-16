import cv2
import numpy as np
import bitarray
import base64

class LSBSteganography:
    """
    Class for hiding and extracting data using the Least Significant Bit (LSB) steganography method.
    This method works by replacing the least significant bit of each color channel in video frames.
    """
    
    @staticmethod
    def text_to_binary(text):
        """Convert text to binary representation"""
        bytes_message = text.encode('utf-8')
        encoded_message = base64.b64encode(bytes_message).decode('utf-8')
        ba = bitarray.bitarray()
        ba.frombytes(encoded_message.encode('utf-8'))

        bit_array = [int(i) for i in ba]
        bit_array_length = len(bit_array)
        length_bits = list(map(int, bin(bit_array_length)[2:].zfill(16)))
        bit_array = length_bits + bit_array
        return bit_array
    
    @staticmethod
    def binary_to_text(binary_data):
        """Convert binary representation to text"""
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
    
    
    def hide_data(self, video_path, output_path, secret_data):
        """
        Hide data within the first frame of a video file using LSB steganography
        
        Args:
            video_path (str): Path to the input video
            output_path (str): Path for the output video with hidden data
            secret_data (str): The secret message to hide
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                return False, "Could not open video file"
            
            frame_count = 0
            first_frame = None

            while video.isOpened():
                ret, frame = video.read()
                if not ret: 
                    break

                if frame_count == 0:
                    first_frame = frame.copy()
                    frame_count += 1
                    continue
                if frame_count == 1:
                    break
            
            if first_frame is None:
                return False, "Could not find a frame to hide data in"
        
            # Convert to a bit array
            bit_array = self.text_to_binary(secret_data)
            print("encoded bit_array: ",bit_array)

            # Ensure the frame has enough capacity
            height, width, _ = first_frame.shape
            
            # Embed data in frame
            bit_index = 0
            for i in range(height):
                for j in range(width):
                    for color_channel in range(3):
                        if bit_index < len(bit_array):
                            # Clear LSB and set it to the secret bit
                            first_frame[i,j,color_channel] = (first_frame[i,j,color_channel] & ~1) | bit_array[bit_index]
                            bit_index += 1
                        else:
                            break
            
            # Write the modified frame and copy remaining frames
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Lossless video codec that works with .mp4
            fps = video.get(cv2.CAP_PROP_FPS)
            size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                   int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            
            out = cv2.VideoWriter(output_path, fourcc, fps, size)
            out.write(first_frame)
            chk_bit_array = []
            for i in range(height):
                for j in range(width):
                    for color_channel in range(3):
                        chk_bit_array.append(first_frame[i,j,color_channel] & 1)
            print("chk_bit_array: ", chk_bit_array)

            if chk_bit_array == bit_array:
                print("Data hidden successfully")
            else:
                print("Data not hidden successfully")
            
            # Reset video to beginning to copy remaining frames
            video.set(cv2.CAP_PROP_POS_FRAMES, 2)
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                out.write(frame)
            
            out.release()
            video.release()
            return True, "Data hidden successfully"
        
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
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                return "Could not open video file"
            
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = video.read()
            print("ret: ", ret)
            if not ret:
                return "Could not read video file"
            
            
            bit_array = []
            for i in range(frame.shape[0]):
                for j in range(frame.shape[1]):
                    for color_channel in range(3):
                        bit_array.append(frame[i,j,color_channel] & 1)
            
            print("decoded bit_array: ", bit_array[0:16])
            # bit_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1,1, 0, 0 ]
            message = self.binary_to_text(bit_array)
            return message  
        
        except Exception as e:
            print(f"Error extracting data: {e}")
            return "Error extracting data" 