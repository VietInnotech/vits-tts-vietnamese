import wave
import numpy as np
from typing import Tuple

def read_wav_file(file_path: str) -> Tuple[np.ndarray, int]:
    """
    Read a WAV file and return the audio data and sample rate.
    
    Args:
        file_path: Path to the WAV file
        
    Returns:
        Tuple of (audio_data, sample_rate)
        audio_data: NumPy array of audio samples
        sample_rate: Sample rate of the audio
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid WAV file
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            # Get audio parameters
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Read audio data
            frames = wav_file.readframes(n_frames)
            
            # Convert to numpy array
            if sample_width == 2:  # 16-bit
                dtype = np.int16
            elif sample_width == 4:  # 32-bit
                dtype = np.int32
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            audio_data = np.frombuffer(frames, dtype=dtype)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_data = audio_data.astype(np.float32) / (2 ** (8 * sample_width - 1))
            
            # If stereo, convert to mono by averaging channels
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels)
                audio_data = np.mean(audio_data, axis=1)
            
            return audio_data, sample_rate
            
    except FileNotFoundError:
        raise FileNotFoundError(f"WAV file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading WAV file {file_path}: {str(e)}")

def write_wav_file(
    file_path: str,
    audio_data: np.ndarray,
    sample_rate: int,
    sample_width: int = 2
) -> None:
    """
    Write audio data to a WAV file.
    
    Args:
        file_path: Path to save the WAV file
        audio_data: NumPy array of audio samples (float32 in range [-1, 1])
        sample_rate: Sample rate of the audio
        sample_width: Sample width in bytes (2 for 16-bit, 4 for 32-bit)
        
    Raises:
        ValueError: If audio_data is not in the correct format
    """
    try:
        # Ensure audio_data is float32 and in range [-1, 1]
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Convert to integer format
        if sample_width == 2:  # 16-bit
            dtype = np.int16
            audio_data_int = (audio_data * (2 ** 15)).astype(dtype)
        elif sample_width == 4:  # 32-bit
            dtype = np.int32
            audio_data_int = (audio_data * (2 ** 31)).astype(dtype)
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        # Write to WAV file
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data_int.tobytes())
            
    except Exception as e:
        raise ValueError(f"Error writing WAV file {file_path}: {str(e)}")

def get_wav_info(file_path: str) -> dict:
    """
    Get information about a WAV file without loading the audio data.
    
    Args:
        file_path: Path to the WAV file
        
    Returns:
        Dictionary containing WAV file information:
        - n_channels: Number of channels
        - sample_width: Sample width in bytes
        - sample_rate: Sample rate
        - n_frames: Number of frames
        - duration: Duration in seconds
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid WAV file
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            duration = n_frames / sample_rate
            
            return {
                'n_channels': n_channels,
                'sample_width': sample_width,
                'sample_rate': sample_rate,
                'n_frames': n_frames,
                'duration': duration
            }
            
    except FileNotFoundError:
        raise FileNotFoundError(f"WAV file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading WAV file info {file_path}: {str(e)}")

def convert_wav_sample_rate(
    input_path: str,
    output_path: str,
    target_sample_rate: int
) -> None:
    """
    Convert a WAV file to a different sample rate.
    
    Args:
        input_path: Path to input WAV file
        output_path: Path to save the converted WAV file
        target_sample_rate: Target sample rate
        
    Raises:
        ValueError: If conversion fails
    """
    try:
        # Read input file
        audio_data, sample_rate = read_wav_file(input_path)
        
        # Skip if sample rate is already the target
        if sample_rate == target_sample_rate:
            return
        
        # Calculate resampling ratio
        ratio = target_sample_rate / sample_rate
        
        # Calculate new length
        new_length = int(len(audio_data) * ratio)
        
        # Resample using linear interpolation
        old_indices = np.arange(len(audio_data))
        new_indices = np.linspace(0, len(audio_data) - 1, new_length)
        
        resampled_data = np.interp(new_indices, old_indices, audio_data)
        
        # Write resampled audio
        write_wav_file(output_path, resampled_data, target_sample_rate)
        
    except Exception as e:
        raise ValueError(f"Error converting sample rate for {input_path}: {str(e)}")

def normalize_wav_file(
    input_path: str,
    output_path: str,
    target_level: float = 0.0
) -> None:
    """
    Normalize a WAV file to a target peak level in dB.
    
    Args:
        input_path: Path to input WAV file
        output_path: Path to save the normalized WAV file
        target_level: Target peak level in dB (default: 0.0 for maximum)
        
    Raises:
        ValueError: If normalization fails
    """
    try:
        # Read input file
        audio_data, sample_rate = read_wav_file(input_path)
        
        # Calculate current peak level
        current_peak = np.max(np.abs(audio_data))
        
        # Skip if already normalized or silent
        if current_peak == 0:
            write_wav_file(output_path, audio_data, sample_rate)
            return
        
        # Calculate target linear scale
        target_linear = 10 ** (target_level / 20)
        
        # Calculate scaling factor
        scale_factor = target_linear / current_peak
        
        # Apply scaling
        normalized_data = audio_data * scale_factor
        
        # Write normalized audio
        write_wav_file(output_path, normalized_data, sample_rate)
        
    except Exception as e:
        raise ValueError(f"Error normalizing WAV file {input_path}: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    # Create a test sine wave
    duration = 1.0  # seconds
    sample_rate = 22050
    frequency = 440  # Hz (A4)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = np.sin(2 * np.pi * frequency * t) * 0.5  # Half amplitude
    
    # Write test WAV file
    test_file = "test_audio.wav"
    write_wav_file(test_file, sine_wave, sample_rate)
    print(f"Created test WAV file: {test_file}")
    
    # Read and verify the file
    audio_data, sr = read_wav_file(test_file)
    print(f"Read WAV file: sample_rate={sr}, duration={len(audio_data)/sr:.2f}s")
    
    # Get file info
    info = get_wav_info(test_file)
    print(f"WAV file info: {info}")
    
    # Test sample rate conversion
    converted_file = "converted_audio.wav"
    convert_wav_sample_rate(test_file, converted_file, 16000)
    print(f"Converted sample rate: {converted_file}")
    
    # Test normalization
    normalized_file = "normalized_audio.wav"
    normalize_wav_file(test_file, normalized_file, -3.0)  # -3 dB
    print(f"Normalized audio: {normalized_file}")