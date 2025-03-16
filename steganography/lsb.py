import cv2
import numpy as np
import bitarray
import base64
import os
import subprocess

def embed_data_into_frame(frame, bit_array):
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


def embed_data_into_video(frames_folder, output_folder, bit_array):
    os.makedirs(output_folder, exist_ok=True)
    frame_list = sorted(os.listdir(frames_folder))

    for idx, frame_file in enumerate(frame_list):
        frame_path = os.path.join(frames_folder, frame_file)
        frame = cv2.imread(frame_path)

        if idx==0 :
          frame = embed_data_into_frame(frame, bit_array)

        cv2.imwrite(os.path.join(output_folder, frame_file), frame)


def extract_frames(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)


    frame_number = 0

    while cap.isOpened():
      ret, frame = cap.read()

      if not ret:
          break

      frame_filename = f"{output_folder}/frame_{frame_number:04d}.png"
      cv2.imwrite(frame_filename, frame)

      frame_number += 1

    cap.release()
    print(f"Extracted {frame_number} frames.")
    return fps
def reconstruct_video(frames_folder, output_video, fps=30):
    frame_list = sorted(os.listdir(frames_folder))

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
        frame_output_path = os.path.join(temp_folder, f"{i:06d}.png")  # Ensuring proper ordering
        cv2.imwrite(frame_output_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # Lossless PNG

    # Use FFmpeg to encode H.265 Lossless
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # Overwrite if exists
        "-framerate", str(fps),
        "-i", os.path.join(temp_folder, "%06d.png"),  # Frame sequence input
        "-c:v", "libx265",  # Use H.265
        "-preset", "slow",  # Better compression
        "-x265-params", "lossless=1",  # Ensure lossless mode
        output_video
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    # Clean up temporary frame folder
    for file in os.listdir(temp_folder):
        os.remove(os.path.join(temp_folder, file))
    os.rmdir(temp_folder)

    print(f"Video saved as {output_video} using H.265 Lossless encoding.")



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

        # Convert to a bit array
        bit_array = [int(i) for i in ba]
        bit_array_length = len(bit_array)
        print("message : ",bit_array)

        # Convert the length of the bit array into binary (e.g., use 16 bits)
        length_bits = list(map(int, bin(bit_array_length)[2:].zfill(16)))

        # Append length bits at the start of the message
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
            bit_array = self.text_to_binary(secret_data)
            frames_dir = "assets/frames"
            fps = extract_frames(video_path, frames_dir)

            frames_data_dir = "assets/frames_with_data"
            embed_data_into_video(frames_dir, frames_data_dir, bit_array)

            reconstruct_video(frames_data_dir, output_path, fps)

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