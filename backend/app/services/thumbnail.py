from typing import BinaryIO, Tuple
import tempfile
import subprocess
import os
from pathlib import Path
import logging
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class ThumbnailService:
    """Video thumbnail generation service"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir())
    
    async def generate_thumbnail(self, video_file: BinaryIO, video_filename: str) -> BytesIO:
        """
        Generate thumbnail from video file
        
        Args:
            video_file: Video file binary stream
            video_filename: Original video filename
            
        Returns:
            BytesIO: Thumbnail image as JPEG
        """
        try:
            # Create temporary files
            temp_video_path = None
            temp_thumbnail_path = None
            
            try:
                # Save video to temporary file
                video_extension = Path(video_filename).suffix.lower()
                temp_video_path = self.temp_dir / f"temp_video_{os.getpid()}{video_extension}"
                
                logger.info(f"Saving video to temporary file: {temp_video_path}")
                with open(temp_video_path, "wb") as temp_video:
                    video_file.seek(0)  # Reset file pointer
                    video_content = video_file.read()
                    temp_video.write(video_content)
                    logger.info(f"Video file saved, size: {len(video_content)} bytes")
                
                # Generate thumbnail path
                temp_thumbnail_path = self.temp_dir / f"temp_thumbnail_{os.getpid()}.jpg"
                logger.info(f"Attempting to generate thumbnail at: {temp_thumbnail_path}")
                
                # Use ffmpeg to generate thumbnail at 2 seconds
                success = await self._extract_thumbnail_with_ffmpeg(
                    str(temp_video_path),
                    str(temp_thumbnail_path),
                    timestamp="00:00:02"
                )
                
                # If thumbnail generation failed, try at 0 seconds
                if not success or not temp_thumbnail_path.exists():
                    logger.info("Retrying thumbnail generation at 0 seconds")
                    success = await self._extract_thumbnail_with_ffmpeg(
                        str(temp_video_path),
                        str(temp_thumbnail_path),
                        timestamp="00:00:00"
                    )
                
                # If still failed, try without seeking
                if not success or not temp_thumbnail_path.exists():
                    logger.info("Retrying thumbnail generation without seeking")
                    success = await self._extract_thumbnail_with_ffmpeg(
                        str(temp_video_path),
                        str(temp_thumbnail_path),
                        timestamp=None
                    )
                
                # If still failed, create a default thumbnail
                if not success or not temp_thumbnail_path.exists():
                    logger.warning(f"Failed to extract thumbnail from {video_filename}, creating default")
                    return self._create_default_thumbnail()
                
                # Read and return thumbnail
                with open(temp_thumbnail_path, "rb") as thumb_file:
                    thumbnail_data = BytesIO(thumb_file.read())
                    thumbnail_data.seek(0)
                    return thumbnail_data
                
            finally:
                # Clean up temporary files
                if temp_video_path and temp_video_path.exists():
                    try:
                        temp_video_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete temp video file: {e}")
                
                if temp_thumbnail_path and temp_thumbnail_path.exists():
                    try:
                        temp_thumbnail_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete temp thumbnail file: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {video_filename}: {e}")
            return self._create_default_thumbnail()
    
    async def _extract_thumbnail_with_ffmpeg(self, video_path: str, thumbnail_path: str, timestamp: str = None) -> bool:
        """
        Extract thumbnail using ffmpeg
        
        Args:
            video_path: Path to video file
            thumbnail_path: Path where thumbnail will be saved
            timestamp: Timestamp to extract frame from (format: HH:MM:SS)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if ffmpeg is available
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.error("ffmpeg is not available")
                return False
            
            # More robust ffmpeg command for various video formats
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-an",  # Disable audio
                "-vcodec", "mjpeg",  # Use MJPEG codec
                "-vframes", "1",
                "-q:v", "2",  # High quality
                "-vf", "scale='min(480,iw)':'min(270,ih)':force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2:color=black",  # Maintain aspect ratio with black padding
                "-y",  # Overwrite output file
            ]
            
            # Add timestamp if specified (after input, before output)
            if timestamp:
                cmd.insert(-1, "-ss")
                cmd.insert(-1, timestamp)
                
            cmd.append(thumbnail_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0 and Path(thumbnail_path).exists():
                file_size = Path(thumbnail_path).stat().st_size
                logger.info(f"Successfully extracted thumbnail at {timestamp}, file size: {file_size} bytes")
                return True
            else:
                logger.error(f"ffmpeg failed with return code {result.returncode}")
                logger.error(f"ffmpeg stderr: {result.stderr}")
                logger.error(f"ffmpeg stdout: {result.stdout}")
                logger.error(f"ffmpeg command: {' '.join(cmd)}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timeout while extracting thumbnail")
            return False
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg.")
            return False
        except Exception as e:
            logger.error(f"Error running ffmpeg: {e}")
            return False
    
    def _create_default_thumbnail(self) -> BytesIO:
        """
        Create a default thumbnail image when video thumbnail extraction fails
        
        Returns:
            BytesIO: Default thumbnail image as JPEG
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a default thumbnail with video icon
            img = Image.new('RGB', (480, 270), color='#2d3748')  # Dark gray background
            draw = ImageDraw.Draw(img)
            
            # Draw a simple video icon
            # Draw play button triangle in center
            center_x, center_y = 240, 135
            triangle_size = 40
            
            # Triangle points (play button)
            triangle = [
                (center_x - triangle_size//2, center_y - triangle_size//2),
                (center_x - triangle_size//2, center_y + triangle_size//2),
                (center_x + triangle_size//2, center_y)
            ]
            
            # Draw white play button
            draw.polygon(triangle, fill='white')
            
            # Draw rectangle around (video frame)
            frame_margin = 60
            draw.rectangle([
                frame_margin, 
                frame_margin, 
                480 - frame_margin, 
                270 - frame_margin
            ], outline='white', width=3)
            
            thumbnail_buffer = BytesIO()
            img.save(thumbnail_buffer, format='JPEG', quality=85)
            thumbnail_buffer.seek(0)
            
            return thumbnail_buffer
            
        except Exception as e:
            logger.error(f"Failed to create default thumbnail: {e}")
            # Return minimal valid JPEG if even default creation fails
            # This is a 1x1 gray pixel JPEG
            minimal_jpeg = BytesIO(
                b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
                b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
                b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
                b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
                b'\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01'
                b'\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00'
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xda\x00\x08\x01\x01\x00'
                b'\x00?\x00\xaa\xff\xd9'
            )
            minimal_jpeg.seek(0)
            return minimal_jpeg

# Global thumbnail service instance
thumbnail_service = ThumbnailService()