import cv2
import numpy as np
import bitarray
import base64
import os
import subprocess

def reconstruct_video(frames_folder, output_video, fps=30):
    frame_list = sorted([f for f in os.listdir(frames_folder) if f.endswith('.png')])

    if not frame_list:
        print("No frames found in the folder.")
        return

    first_frame = cv2.imread(os.path.join(frames_folder, frame_list[0]))
    height, width, _ = first_frame.shape

    # Save frames as lossless PNG (if not already PNG)
    temp_folder = "temp_png_frames"
    os.makedirs(temp_folder, exist_ok=True)

    for i, frame_file in enumerate(frame_list):
        frame_path = os.path.join(frames_folder, frame_file)
        frame = cv2.imread(frame_path)
        frame_output_path = os.path.join(temp_folder, f"{i:06d}.png")
        cv2.imwrite(frame_output_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    # On macOS, ensure ffmpeg is installed and use a more compatible encoding
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_folder, "%06d.png"),
        "-c:v", "prores_ks",  # Apple ProRes codec (compatible with macOS)
        "-profile:v", "4444",  # ProRes 4444 (high quality, lossless alpha)
        "-pix_fmt", "yuva444p10le",  # 10-bit color depth with alpha
        "-vendor", "apl0",
        "-quant_mat", "hq",
        output_video
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback to H.264 if ProRes fails or ffmpeg not installed properly
        print("ProRes encoding failed, falling back to H.264 lossless...")
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", os.path.join(temp_folder, "%06d.png"),
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-qp", "0",  # Lossless H.264
            "-pix_fmt", "yuv420p",
            output_video
        ]
        subprocess.run(ffmpeg_cmd, check=True)

    # Clean up temporary frame folder
    for file in os.listdir(temp_folder):
        os.remove(os.path.join(temp_folder, file))
    os.rmdir(temp_folder)

    print(f"Video saved as {output_video}")


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
            
            # Create frames directory if it doesn't exist
            import os
            frames_dir = "assets/frames"
            os.makedirs(frames_dir, exist_ok=True)
            
            # Extract and save all frames
            frames = []
            frame_count = 0
            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break
                    
                frames.append(frame.copy())
                # Save frame
                cv2.imwrite(os.path.join(frames_dir, f"frame_{frame_count}.png"), frame)
                frame_count += 1
            
            if not frames:
                return False, "Could not find any frames in video"
                
            # Get first frame to encode message
            first_frame = frames[0]
        
            # Convert message to bit array
            bit_array = self.text_to_binary(secret_data)
            print("encoded bit_array: ", bit_array)

            # Get frame dimensions
            # height, width, _ = first_frame.shape
            
            # # Embed data in first frame
            # bit_index = 0
            # for i in range(height):
            #     for j in range(width):
            #         for color_channel in range(3):
            #             if bit_index < len(bit_array):
            #                 # Clear LSB and set it to the secret bit
            #                 first_frame[i,j,color_channel] = (first_frame[i,j,color_channel] & ~1) | bit_array[bit_index]
            #                 bit_index += 1
            #             else:
            #                 break
                  
            reconstruct_video(frames_dir, output_path, fps=30)

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