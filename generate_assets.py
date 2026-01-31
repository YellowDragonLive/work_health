import os
from PIL import Image, ImageDraw
import wave
import math
import struct

def create_icon(path="icon.png"):
    """Creates a simple 64x64 icon with a green circle."""
    size = (64, 64)
    image = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    # Draw a green circle
    draw.ellipse((4, 4, 60, 60), fill=(0, 200, 100), outline=(0, 100, 50))
    image.save(path)
    print(f"Created icon at {path}")

def create_beep_wav(path="default_music.wav", duration=1.0, freq=440.0):
    """Creates a simple sine wave beep sound."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    amplitude = 16000
    
    with wave.open(path, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            # value = int(amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
            # Make it a bit more pleasant (major chord arpeggio-ish)
            if i < n_samples / 3:
                f = freq
            elif i < 2 * n_samples / 3:
                f = freq * 1.25 # Major third
            else:
                f = freq * 1.5  # Perfect fifth
                
            value = int(amplitude * math.sin(2 * math.pi * f * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)
            
    print(f"Created default music at {path}")

if __name__ == "__main__":
    # Create 'assets' directory if strict structure is needed, 
    # but for now we put them in root or src based on usage. 
    # Let's put them in a dedicated assets folder relative to where main.py will run.
    target_dir = os.path.join(os.getcwd(), "src", "assets")
    os.makedirs(target_dir, exist_ok=True)
    
    create_icon(os.path.join(target_dir, "icon.png"))
    create_beep_wav(os.path.join(target_dir, "default_music.wav"))
