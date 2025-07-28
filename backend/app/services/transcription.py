import openai
import os
from typing import BinaryIO, Optional
from dotenv import load_dotenv
import tempfile
import asyncio

load_dotenv()

class TranscriptionService:
    """Service for audio transcription using OpenAI Whisper"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.use_dummy = not self.api_key or self.api_key == "your_openai_api_key_here"
        
        if not self.use_dummy:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            print("OpenAI API key not configured, using dummy transcription")
    
    async def transcribe_audio(self, audio_file: BinaryIO, language: str = "ja") -> str:
        """
        Transcribe audio file using OpenAI Whisper
        
        Args:
            audio_file: Audio file binary data
            language: Language code (default: "ja" for Japanese)
            
        Returns:
            Transcribed text
        """
        if self.use_dummy:
            # Return dummy transcription for development
            print("Using dummy transcription")
            return "こちらはダミーの文字起こし結果です。スイングの改善点について説明しています。アドレスの姿勢を意識して、体重移動をスムーズに行いましょう。"
        
        try:
            # Whisper API requires a file-like object with a name
            # Create temporary file if needed
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                # Copy audio data to temporary file
                audio_file.seek(0)
                temp_file.write(audio_file.read())
                temp_file.flush()
                
                # Reset the audio file pointer
                audio_file.seek(0)
                
                # Transcribe using Whisper
                with open(temp_file.name, "rb") as audio:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language=language,
                        prompt="これはゴルフのコーチングセッションの音声です。ゴルフ用語や技術的な指導内容が含まれています。",
                        response_format="text"
                    )
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return transcript if isinstance(transcript, str) else transcript.text
                
        except Exception as e:
            print(f"Transcription failed: {e}")
            raise Exception(f"音声の文字起こしに失敗しました: {str(e)}")
    
    async def transcribe_audio_with_timestamps(self, audio_file: BinaryIO, language: str = "ja") -> dict:
        """
        Transcribe audio with timestamp information
        
        Args:
            audio_file: Audio file binary data
            language: Language code (default: "ja" for Japanese)
            
        Returns:
            Dictionary with text and segments with timestamps
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                audio_file.seek(0)
                temp_file.write(audio_file.read())
                temp_file.flush()
                
                audio_file.seek(0)
                
                with open(temp_file.name, "rb") as audio:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language=language,
                        prompt="これはゴルフのコーチングセッションの音声です。ゴルフ用語や技術的な指導内容が含まれています。",
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                
                os.unlink(temp_file.name)
                
                return {
                    "text": transcript.text,
                    "language": transcript.language,
                    "duration": transcript.duration,
                    "segments": [
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text
                        }
                        for segment in transcript.segments
                    ]
                }
                
        except Exception as e:
            print(f"Transcription with timestamps failed: {e}")
            raise Exception(f"タイムスタンプ付き文字起こしに失敗しました: {str(e)}")
    
    async def validate_audio_format(self, audio_file: BinaryIO) -> bool:
        """
        Validate if audio file format is supported by Whisper
        
        Args:
            audio_file: Audio file to validate
            
        Returns:
            True if format is supported
        """
        if self.use_dummy:
            # Always return True for dummy mode
            return True
            
        # Whisper supports: m4a, mp3, mp4, mpeg, mpga, wav, webm
        supported_formats = ['.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.wav', '.webm']
        
        # Get file name if available
        filename = getattr(audio_file, 'name', '')
        if filename:
            file_ext = os.path.splitext(filename.lower())[1]
            return file_ext in supported_formats
        
        # If no filename, assume it's valid (let Whisper handle validation)
        return True

# Global transcription service instance
transcription_service = TranscriptionService()