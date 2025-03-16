import cv2
import numpy as np
import subprocess
import os
from tqdm import tqdm
import wave
from pathlib import Path

class VideoInVideoSteganography:
    """
    Class for hiding one video inside another video using LSB steganography.
    This implementation handles both video and audio components.
    """
    
    def __init__(self):
        """Initialize the video-in-video steganography class"""
        # Create temporary directories if they don't exist
        self.enc_dir = Path("enc")
        self.out_dir = Path("out")
        self.enc_dir.mkdir(exist_ok=True)
        self.out_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def resize(src, w=None, h=None, ar=None):
        """
        Resize an image while maintaining aspect ratio
        
        Args:
            src: Source image
            w: Target width (optional)
            h: Target height (optional)
            ar: Aspect ratio (optional)
            
        Returns:
            Resized image
        """
        if w is not None and h is not None:
            return cv2.resize(src, (w, h))
        assert(ar is not None)
        if w is not None:
            return cv2.resize(src, (w, int(w/ar)))
        if h is not None:
            return cv2.resize(src, (int(h*ar), h))
    
    def encode_audio(self, cover_audio_path, secret_audio_path, output_path):
        """
        Encode secret audio into cover audio using LSB
        
        Args:
            cover_audio_path: Path to cover audio file
            secret_audio_path: Path to secret audio file
            output_path: Path to save encoded audio
        """
        with wave.open(output_path, 'wb') as e:
            s = wave.open(secret_audio_path, 'rb')
            c = wave.open(cover_audio_path, 'rb')
            
            s_frames = np.array(list(s.readframes(s.getnframes())), dtype='uint8')
            c_frames = np.array(list(c.readframes(c.getnframes())), dtype='uint8')
            
            # Make frame lengths equal
            if s_frames.shape[0] > c_frames.shape[0]:
                c_frames = np.concatenate((c_frames, np.zeros((s_frames.shape[0]-c_frames.shape[0],), dtype='uint8')), axis=0)
            elif s_frames.shape[0] < c_frames.shape[0]:
                s_frames = np.concatenate((s_frames, np.zeros((c_frames.shape[0]-s_frames.shape[0],), dtype='uint8')), axis=0)
            
            # Encode audio: use upper 4 bits of secret in lower 4 bits of cover
            enc_frames = (c_frames & 0b11110000) | (s_frames & 0b11110000) >> 4
            
            e.setparams(s.getparams())
            e.writeframes(np.ndarray.tobytes(enc_frames))
            
            s.close()
            c.close()
    
    def hide_video(self, cover_path, secret_path, output_path):
        """
        Hide a secret video inside a cover video
        
        Args:
            cover_path (str): Path to the cover video
            secret_path (str): Path to the secret video
            output_path (str): Path to save the output video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open videos
            src = cv2.VideoCapture(cover_path)
            sec = cv2.VideoCapture(secret_path)
            
            # Get video properties
            src_w = int(src.get(3))
            src_h = int(src.get(4))
            src_fps = src.get(cv2.CAP_PROP_FPS)
            src_frame_cnt = src.get(cv2.CAP_PROP_FRAME_COUNT)
            
            sec_w = int(sec.get(3))
            sec_h = int(sec.get(4))
            sec_fps = sec.get(cv2.CAP_PROP_FPS)
            sec_frame_cnt = sec.get(cv2.CAP_PROP_FRAME_COUNT)
            
            # Check if cover video is long enough
            if src_frame_cnt < sec_frame_cnt:
                print("Cover video must be longer than secret video")
                return False
            
            # Extract audio components
            sec_duration = sec_frame_cnt/sec_fps
            subprocess.call(f"ffmpeg -ss 0 -t {sec_duration} -i {cover_path} {self.enc_dir}/cvr.wav", shell=True)
            subprocess.call(f"ffmpeg -ss 0 -t {sec_duration} -i {secret_path} {self.enc_dir}/scr.wav", shell=True)
            
            # Encode audio
            self.encode_audio(f"{self.enc_dir}/cvr.wav", f"{self.enc_dir}/scr.wav", f"{self.enc_dir}/enc.wav")
            
            # Frame counter
            fn = 0
            
            # Process frames with progress bar
            pbar = tqdm(total=sec_frame_cnt*2, unit='frames')
            
            while True:
                _, src_frame = src.read()
                ret, sec_frame = sec.read()
                
                if not ret:
                    break
                
                # Get aspect ratios
                src_ar = src_w/src_h
                sec_ar = sec_w/sec_h
                
                # Resize secret frame to fit cover frame
                if src_ar == sec_ar and src_frame.shape < sec_frame.shape:
                    sec_frame = self.resize(sec_frame, src_w, src_h)
                elif src_ar != sec_ar and (src_w < sec_w or src_h < sec_h):
                    if sec_w > sec_h:
                        sec_frame = self.resize(sec_frame, w=src_w, ar=sec_ar)
                        if sec_frame.shape[0] > src_h:
                            sec_frame = self.resize(sec_frame, h=src_h, ar=sec_ar)
                    else:
                        sec_frame = self.resize(sec_frame, h=src_h, ar=sec_ar)
                        if sec_frame.shape[1] > src_w:
                            sec_frame = self.resize(sec_frame, w=src_w, ar=sec_ar)
                
                # Fill remaining pixels with black
                sec_frame = cv2.hconcat([sec_frame, np.zeros((sec_frame.shape[0], src_w-sec_frame.shape[1], 3), dtype='uint8')])
                sec_frame = cv2.vconcat([sec_frame, np.zeros((src_h-sec_frame.shape[0], sec_frame.shape[1], 3), dtype='uint8')])
                
                # Encode frames using LSB (2 bits)
                fn += 1
                encrypted_img = (src_frame & 0b11111100) | (sec_frame >> 4 & 0b00000011)
                cv2.imwrite(f"{self.enc_dir}/{fn}.png", encrypted_img)
                
                # Encode frames using LSB (3rd and 4th bits)
                fn += 1
                encrypted_img = (src_frame & 0b11111100) | (sec_frame >> 6)
                cv2.imwrite(f"{self.enc_dir}/{fn}.png", encrypted_img)
                
                pbar.update(2)
            
            pbar.close()
            src.release()
            sec.release()
            
            # Create final video with audio
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Save using FFmpeg (lossless)
            save_cmd = f"ffmpeg -framerate {src_fps*2} -i {self.enc_dir}/%d.png -i {self.enc_dir}/enc.wav -c:v copy -c:a copy {output_path}"
            subprocess.call(save_cmd, shell=True)
            
            # Cleanup
            subprocess.call(f"rm -r {self.enc_dir}", shell=True)
            
            return True
            
        except Exception as e:
            print(f"Error hiding video: {str(e)}")
            return False
    
    def extract_video(self, stego_path, output_path):
        """
        Extract the hidden video from a stego video
        
        Args:
            stego_path (str): Path to the stego video
            output_path (str): Path to save the extracted video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the encrypted video file
            enc = cv2.VideoCapture(stego_path)
            enc_w = int(enc.get(3))
            enc_h = int(enc.get(4))
            enc_fps = enc.get(cv2.CAP_PROP_FPS)
            enc_frame_cnt = enc.get(cv2.CAP_PROP_FRAME_COUNT)
            
            # Video writer for decoding secret video
            # Note: FPS is halved since we used 2 frames to store 1 secret frame
            out = cv2.VideoWriter(f"{self.enc_dir}/decrypted_secret.avi", 
                                cv2.VideoWriter_fourcc(*"MJPG"), 
                                enc_fps/2, 
                                (enc_w, enc_h))
            
            # Extract audio from stego video
            subprocess.call(f"ffmpeg -i {stego_path} {self.enc_dir}/enc.wav", shell=True)
            
            # Decode audio file
            with wave.open(f"{self.enc_dir}/dec.wav", 'wb') as d:
                e = wave.open(f"{self.enc_dir}/enc.wav", 'rb')
                e_frames = np.array(list(e.readframes(e.getnframes())), dtype='uint8')
                
                # Decrypt audio: shift lower 4 bits to upper 4 bits
                dec_frames = (e_frames & 0b00001111) << 4
                
                d.setparams(e.getparams())
                d.writeframes(np.ndarray.tobytes(dec_frames))
                e.close()
            
            # Frame counter
            fn = 0
            
            # Process frames with progress bar
            pbar = tqdm(total=enc_frame_cnt, unit='frames')
            
            while True:
                ret, frame = enc.read()
                
                if not ret:
                    break
                
                fn += 1
                
                # For even frames, extract lower 2 bits and shift left by 4
                # For odd frames, extract lower 2 bits, shift left by 6 and combine with previous frame
                if fn % 2:
                    decrypted_frame = (frame & 0b00000011) << 4
                else:
                    decrypted_frame = decrypted_frame | (frame & 0b00000011) << 6
                    out.write(decrypted_frame)
                
                pbar.update(1)
            
            pbar.close()
            enc.release()
            out.release()
            
            # Delete output file if it already exists
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Combine video and audio using FFmpeg
            save_cmd = f"ffmpeg -i {self.enc_dir}/decrypted_secret.avi -i {self.enc_dir}/dec.wav -c:v copy {output_path}"
            subprocess.call(save_cmd, shell=True)
            
            # Cleanup temporary files
            subprocess.call(f"rm -r {self.enc_dir}", shell=True)
            
            return True
            
        except Exception as e:
            print(f"Error extracting video: {str(e)}")
            return False 