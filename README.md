# Video Steganography Tool

## Overview
A powerful tool for hiding secret messages inside video files using different steganographic techniques. This application features a user-friendly PyQt5-based GUI that allows users to encode messages into videos and later extract them.

## Features
✅ **Multiple Steganography Methods**
  - **LSB (Least Significant Bit)** - Hides data by replacing the least significant bits of pixel values
  - **VIV (Video In Video)** - Embeds a video file within another video

✅ **User-Friendly Interface**
  - Intuitive GUI for encoding and decoding operations
  - Real-time capacity calculation
  - Progress tracking during operations

✅ **Security Features**
  - Optional password protection for hidden messages
  - Robust data hiding algorithms

## Installation

### Prerequisites
- Python 3.8 or higher
- Dependencies listed in requirements.txt

### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/video-steganography.git
   cd video-steganography
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application
Execute the main script:
```bash
python main.py
```

### Encoding a Message
1. Choose a steganography method (LSB or VIV)
2. Click "Browse" to select an input video file
3. Enter your secret message in the text area or Browse for secret video file
6. Click "Encode Message" to start the process
7. Wait for the encoding to complete and save the output video

### Decoding a Message
1. Select the "Decode Message" tab
2. Choose Steganography method (LSB or VIV) [must match the method used for encoding]
3. Click "Browse" to select a video with a hidden message
4. [for VIV] Enter output folder to save the extracted video
5. Click "Decode Message" to extract the hidden data
6. The decoded message will appear in the text area or the extracted video will be saved in the output folder 

## Technical Details

### Steganography Methods

#### LSB (Least Significant Bit)
LSB replaces the least significant bits of each color channel (RGB) in the video frames with bits from the secret message. This method offers high capacity but may be less resistant to video processing operations.

#### VIV (Video In Video)
VIV embeds a video file within another video by dividing the frames of the secret video into blocks and hiding them in the frames of the cover video. This method provides better security and robustness but has lower capacity compared to LSB.

## Development

### Running Tests
```bash
python -m unittest discover tests
```

### Project Structure
- `main.py` - Application entry point
- `steganography/` - Steganography algorithm implementations
- `gui/` - PyQt5 user interface components
- `utils/` - Utility functions and helpers
- `tests/` - Unit tests
- `assets/` - Application resources

