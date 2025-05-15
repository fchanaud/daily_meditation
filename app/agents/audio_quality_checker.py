import os
from pathlib import Path
from pydub import AudioSegment
import tempfile

class AudioQualityCheckerAgent:
    """
    Agent for checking the quality of downloaded meditation audio files.
    Validates audio files based on duration, bitrate, and other quality metrics.
    """
    
    def __init__(self):
        """
        Initialize the audio quality checker agent.
        """
        # Minimum and maximum acceptable duration for meditation audio (in milliseconds)
        self.min_duration_ms = 5 * 60 * 1000  # 5 minutes
        self.max_duration_ms = 15 * 60 * 1000  # 15 minutes
        
        # Minimum acceptable bitrate (in kbps)
        self.min_bitrate_kbps = 64
        
        # Minimum acceptable sample rate (in Hz)
        self.min_sample_rate = 22050
    
    async def check_quality(self, audio_path: str) -> dict:
        """
        Check the quality of an audio file.
        
        Args:
            audio_path: Path to the audio file to check
            
        Returns:
            Dictionary containing quality check results and whether the file passes
        """
        result = {
            "is_acceptable": False,
            "issues": [],
            "details": {}
        }
        
        try:
            # Check if file exists
            if not os.path.exists(audio_path) or not os.path.isfile(audio_path):
                result["issues"].append("File does not exist")
                return result
            
            # Check if file is empty
            if os.path.getsize(audio_path) == 0:
                result["issues"].append("File is empty")
                return result
            
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get audio properties
            duration_ms = len(audio)
            channels = audio.channels
            sample_width = audio.sample_width
            frame_rate = audio.frame_rate
            
            # Calculate bitrate (approximate)
            file_size_bits = os.path.getsize(audio_path) * 8
            duration_seconds = duration_ms / 1000
            bitrate_kbps = int((file_size_bits / duration_seconds) / 1000) if duration_seconds > 0 else 0
            
            # Store details
            result["details"] = {
                "duration_seconds": round(duration_seconds, 2),
                "channels": channels,
                "sample_width_bytes": sample_width,
                "sample_rate_hz": frame_rate,
                "bitrate_kbps": bitrate_kbps
            }
            
            # Check duration
            if duration_ms < self.min_duration_ms:
                result["issues"].append(f"Duration too short: {duration_ms/1000:.2f}s (min: {self.min_duration_ms/1000}s)")
            elif duration_ms > self.max_duration_ms:
                result["issues"].append(f"Duration too long: {duration_ms/1000:.2f}s (max: {self.max_duration_ms/1000}s)")
                
            # Check bitrate
            if bitrate_kbps < self.min_bitrate_kbps:
                result["issues"].append(f"Bitrate too low: {bitrate_kbps}kbps (min: {self.min_bitrate_kbps}kbps)")
                
            # Check sample rate
            if frame_rate < self.min_sample_rate:
                result["issues"].append(f"Sample rate too low: {frame_rate}Hz (min: {self.min_sample_rate}Hz)")
            
            # Check for audio content (not just silence)
            # Calculate average volume (dBFS)
            if len(audio) > 0:
                volume_dbfs = audio.dBFS
                if volume_dbfs < -50:  # Very quiet audio might be just silence
                    result["issues"].append(f"Audio may be too quiet: {volume_dbfs:.2f} dBFS")
                result["details"]["volume_dbfs"] = round(volume_dbfs, 2)
            
            # Set the overall acceptable status
            result["is_acceptable"] = len(result["issues"]) == 0
            
        except Exception as e:
            result["issues"].append(f"Error analyzing audio: {str(e)}")
        
        return result 