"""
AudioQualityCheckerAgent module for validating meditation audio quality.
This agent ensures audio files meet quality standards for meditation.
"""

import os
import logging
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import mediainfo
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioQualityCheckerAgent:
    """
    Agent for checking the quality of meditation audio files.
    Validates audio files for appropriate duration, bitrate, and other quality metrics.
    """
    
    def __init__(self):
        """
        Initialize the audio quality checker agent with quality standards.
        """
        # Target duration for meditation audio files (in milliseconds)
        self.target_duration_ms = 10 * 60 * 1000  # 10 minutes
        
        # Acceptable duration range (8-12 minutes for 10-minute meditations)
        self.min_duration_ms = 8 * 60 * 1000  # 8 minutes
        self.max_duration_ms = 12 * 60 * 1000  # 12 minutes
        
        # Fallback wider duration range (5-15 minutes)
        self.fallback_min_duration_ms = 5 * 60 * 1000  # 5 minutes
        self.fallback_max_duration_ms = 15 * 60 * 1000  # 15 minutes
        
        # Minimum acceptable bitrate (in kbps)
        self.min_bitrate_kbps = 64
        
        # Minimum acceptable sample rate (in Hz)
        self.min_sample_rate_hz = 22050
        
        # Maximum duration for intros/outros (in milliseconds)
        self.max_silence_intro_ms = 15 * 1000  # 15 seconds
        self.max_silence_outro_ms = 5 * 1000  # 5 seconds
    
    async def check_quality(self, audio_path):
        """
        Check the quality of the audio file.
        
        Args:
            audio_path: Path to the audio file to check
            
        Returns:
            Tuple of (is_quality_acceptable, details_dict)
        """
        logger.info(f"Checking quality of audio file: {audio_path}")
        
        # Check if file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            return False, {"error": "File does not exist"}
        
        # Check if file size is reasonable
        file_size = os.path.getsize(audio_path)
        if file_size < 1024:  # Files smaller than 1KB are suspicious
            logger.error(f"Audio file is too small: {file_size} bytes")
            return False, {"error": "File too small", "size_bytes": file_size}
        
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get basic audio properties
            duration_ms = len(audio)
            channels = audio.channels
            sample_width = audio.sample_width * 8  # Convert to bits
            frame_rate = audio.frame_rate
            
            # Get more detailed info using mediainfo
            media_info = mediainfo(audio_path)
            bitrate_raw = media_info.get('bit_rate', '0')
            
            # Parse bitrate (may be in format like '192000' or '192k')
            try:
                if 'k' in bitrate_raw.lower():
                    bitrate_kbps = int(float(bitrate_raw.lower().replace('k', '')))
                else:
                    bitrate_kbps = int(int(bitrate_raw) / 1000)
            except (ValueError, AttributeError):
                # If we can't parse the bitrate, estimate it from file size
                duration_seconds = duration_ms / 1000
                if duration_seconds > 0:
                    bitrate_kbps = int((file_size * 8) / (duration_seconds * 1000))
                else:
                    bitrate_kbps = 0
            
            # Create the details dictionary
            details = {
                "duration_minutes": round(duration_ms / (60 * 1000), 2),
                "channels": channels,
                "bit_depth": sample_width,
                "sample_rate_hz": frame_rate,
                "bitrate_kbps": bitrate_kbps,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
            
            # Check for audio quality issues
            issues = []
            
            # Check duration - strict check first
            if duration_ms < self.min_duration_ms or duration_ms > self.max_duration_ms:
                msg = f"Duration ({details['duration_minutes']} min) outside ideal range (8-12 min)"
                issues.append(msg)
                
                # Fallback check - wider range
                if duration_ms < self.fallback_min_duration_ms or duration_ms > self.fallback_max_duration_ms:
                    msg = f"Duration ({details['duration_minutes']} min) outside acceptable range (5-15 min)"
                    issues.append(msg)
            
            # Check bitrate
            if bitrate_kbps < self.min_bitrate_kbps:
                issues.append(f"Bitrate too low: {bitrate_kbps} kbps (min: {self.min_bitrate_kbps} kbps)")
            
            # Check sample rate
            if frame_rate < self.min_sample_rate_hz:
                issues.append(f"Sample rate too low: {frame_rate} Hz (min: {self.min_sample_rate_hz} Hz)")
            
            # Check for valid audio content (not just silence)
            if audio.dBFS < -45:
                issues.append(f"Audio may be too quiet: {audio.dBFS:.2f} dBFS")
            details["volume_dbfs"] = round(audio.dBFS, 2)
            
            # Check for long silent intros/outros
            silence_threshold = -40  # dB
            chunk_size = 1000  # 1 second chunks
            
            # Check intro silence
            intro_silence_ms = 0
            for i in range(0, min(30000, duration_ms), chunk_size):  # Check first 30 seconds max
                chunk = audio[i:i+chunk_size]
                if chunk.dBFS < silence_threshold:
                    intro_silence_ms += chunk_size
                else:
                    break
            
            if intro_silence_ms > self.max_silence_intro_ms:
                issues.append(f"Long silent intro: {intro_silence_ms/1000:.1f} seconds")
            details["intro_silence_seconds"] = round(intro_silence_ms/1000, 1)
            
            # Check outro silence
            outro_silence_ms = 0
            for i in range(max(0, duration_ms - 10000), duration_ms, chunk_size):  # Check last 10 seconds
                chunk = audio[i:min(i+chunk_size, duration_ms)]
                if chunk.dBFS < silence_threshold:
                    outro_silence_ms += chunk_size
                else:
                    outro_silence_ms = 0  # Reset if we encounter non-silence
            
            if outro_silence_ms > self.max_silence_outro_ms:
                issues.append(f"Long silent outro: {outro_silence_ms/1000:.1f} seconds")
            details["outro_silence_seconds"] = round(outro_silence_ms/1000, 1)
            
            # Determine if audio is acceptable based on issues
            is_acceptable = len(issues) == 0
            
            # For minor issues, still consider acceptable
            if len(issues) == 1 and (
                "outside ideal range" in issues[0] or 
                "silent intro" in issues[0] or 
                "silent outro" in issues[0]
            ):
                is_acceptable = True
                
            details["issues"] = issues
            details["is_acceptable"] = is_acceptable
            
            logger.info(f"Audio quality check results: acceptable={is_acceptable}, issues={len(issues)}")
            return is_acceptable, details
            
        except Exception as e:
            logger.error(f"Error checking audio quality: {str(e)}")
            return False, {"error": f"Failed to analyze audio: {str(e)}"}
    
    async def trim_audio_if_needed(self, audio_path, target_duration_ms=None):
        """
        Trim audio file to target duration if it's too long.
        
        Args:
            audio_path: Path to the audio file
            target_duration_ms: Target duration in milliseconds (defaults to 10 minutes)
            
        Returns:
            Path to the trimmed audio file (same as input if no trimming needed)
        """
        if target_duration_ms is None:
            target_duration_ms = self.target_duration_ms
            
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Get duration
            duration_ms = len(audio)
            
            # If duration is within acceptable range, don't trim
            if duration_ms <= self.max_duration_ms:
                return audio_path
                
            logger.info(f"Trimming audio file from {duration_ms/1000:.1f}s to {target_duration_ms/1000:.1f}s")
            
            # Trim to target duration
            trimmed_audio = audio[:target_duration_ms]
            
            # Create output filename
            base_path = os.path.splitext(audio_path)[0]
            output_path = f"{base_path}_trimmed.mp3"
            
            # Export trimmed audio
            trimmed_audio.export(output_path, format="mp3", bitrate="192k")
            
            logger.info(f"Audio trimmed and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error trimming audio: {str(e)}")
            return audio_path  # Return original path if trimming fails 