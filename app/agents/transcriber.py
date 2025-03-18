from langchain_openai import OpenAI
from openai import OpenAI as DirectOpenAI
from app.models import State
import os
import tempfile

class Transcriber:
    """Transcribe audio content in messages before processing"""
    
    def __init__(self):
        # Initialize the direct OpenAI client for whisper
        self.client = DirectOpenAI()
    
    def __call__(self, state: State) -> State:
        """
        Check for audio in the message and transcribe it
        """
        # If no media or no audio, just return state unchanged
        if not state.message.media_items:
            return state
            
        # Check if any media item is audio
        audio_items = [media for media in state.message.media_items 
                      if media["type"].startswith("audio/")]
        
        if not audio_items:
            return state
            
        # Process the first audio item (could extend to handle multiple)
        audio = audio_items[0]
        
        print(f"Transcribing audio from {state.message.sender}")
        
        try:
            # Write the base64 decoded audio to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                # Write the binary audio data to the file
                temp_path = temp_audio.name
                
                # If we have file_path, use it
                if "file_path" in audio and os.path.exists(audio["file_path"]):
                    temp_path = audio["file_path"]
                    print(f"Using existing audio file at {temp_path}")
                
            # Transcribe using the Whisper API
            with open(temp_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                
            transcription = transcript.text
            print(f"Transcription: {transcription}")
            
            # Update the message body with the transcription
            # If there was already text, append the transcription
            if state.message.body:
                state.message.body = f"{state.message.body}\n[Audio Transcription: {transcription}]"
            else:
                state.message.body = transcription
        
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            # If transcription fails, add a note to the message
            if state.message.body:
                state.message.body = f"{state.message.body}\n[Audio transcription failed]"
            else:
                state.message.body = "[Audio transcription failed. Please try again or describe your meal in text.]"
        
        return state 