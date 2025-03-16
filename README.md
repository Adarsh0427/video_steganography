# Video Steganography Tool

## Overview
A powerful tool for hiding secret messages inside video files using different steganographic techniques. This application features a user-friendly PyQt5-based GUI that allows users to encode messages into videos and later extract them.

## Features
✅ **Multiple Steganography Methods**
  - **LSB (Least Significant Bit)** - Hides data by replacing the least significant bits of pixel values
  - **DCT (Discrete Cosine Transform)** - Uses frequency domain transformation to hide data more robustly

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

   Alternatively, if you use Poetry:
   ```bash
   poetry install
   ```

## Usage

### Running the Application
Execute the main script:
```bash
python main.py
```

Or if using Poetry:
```bash
poetry run video-steg
```

### Encoding a Message
1. Select the "Encode Message" tab
2. Click "Browse" to select an input video file
3. Enter your secret message in the text area
4. Choose a steganography method (LSB or DCT)
5. Optionally enable password protection
6. Click "Encode Message" to start the process
7. Wait for the encoding to complete and save the output video

### Decoding a Message
1. Select the "Decode Message" tab
2. Click "Browse" to select a video with a hidden message
3. Choose the same steganography method that was used for encoding
4. Enter the password if one was used during encoding
5. Click "Decode Message" to extract the hidden data
6. The decoded message will appear in the text area

## Technical Details

### Steganography Methods

#### LSB (Least Significant Bit)
LSB replaces the least significant bits of each color channel (RGB) in the video frames with bits from the secret message. This method offers high capacity but may be less resistant to video processing operations.

#### DCT (Discrete Cosine Transform)
DCT embeds data in the frequency domain by modifying coefficients after applying a discrete cosine transform to 8x8 pixel blocks. This method is more robust against compression and processing but offers lower capacity.

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

