"""
Text-to-Speech Converter Application

This module provides functionality to convert text files into speech using the Nix-TTS model.
It handles text preprocessing, chunking, and audio generation with proper silence intervals.
"""

from nix.models.TTS import NixTTSInference
import scipy.io.wavfile as wavfile
import numpy as np
from typing import List, Optional
import os

class TextToSpeechConverter:
    """
    A class to handle text-to-speech conversion using Nix-TTS.
    
    Attributes:
        nix: NixTTSInference instance
        sample_rate: Audio sample rate (default: 22050 Hz)
        chunk_size: Maximum size of text chunks for processing
        silence_duration: Duration of silence between chunks in seconds
    """

    def __init__(self, model_dir: str, chunk_size: int = 50, 
                 sample_rate: int = 22050, silence_duration: float = 0.1):
        """
        Initialize the TTS converter.

        Args:
            model_dir: Path to the Nix-TTS model directory
            chunk_size: Maximum size of text chunks
            sample_rate: Audio sample rate in Hz
            silence_duration: Duration of silence between chunks in seconds
        """
        self.nix = NixTTSInference(model_dir=model_dir)
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_duration = silence_duration

    def process_chunk(self, text: str) -> np.ndarray:
        """Process a single chunk of text into audio."""
        try:
            c, c_length, _ = self.nix.tokenize(text)
            return self.nix.vocalize(c, c_length)[0,0]
        except Exception as e:
            print(f"Error processing chunk: {text[:50]}...")
            raise e

    def _split_sentence(self, sentence: str) -> List[str]:
        """Split a long sentence into smaller chunks."""
        chunks = []
        words = sentence.split()
        temp_chunk = []
        temp_size = 0

        for word in words:
            if temp_size + len(word) > self.chunk_size and temp_chunk:
                chunks.append(' '.join(temp_chunk) + '.')
                temp_chunk = [word]
                temp_size = len(word)
            else:
                temp_chunk.append(word)
                temp_size += len(word) + 1

        if temp_chunk:
            chunks.append(' '.join(temp_chunk) + '.')
        return chunks

    def split_text_into_chunks(self, text: str) -> List[str]:
        """Split input text into processable chunks."""
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in text.split('. '):
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) > self.chunk_size:
                chunks.extend(self._split_sentence(sentence))
            else:
                if current_size + len(sentence) > self.chunk_size and current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_size = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_size += len(sentence)

        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        return chunks

    def convert(self, input_file: str, output_file: str) -> None:
        """
        Convert text from input file to speech and save as audio file.

        Args:
            input_file: Path to input text file
            output_file: Path to output WAV file
        """
        try:
            # Read and preprocess input text
            with open(input_file, 'r') as file:
                input_text = ' '.join(file.read().strip().split())

            # Split into chunks and process
            chunks = self.split_text_into_chunks(input_text)
            print(f"Processing {len(chunks)} chunks...")

            # Generate audio for each chunk
            audio_chunks = []
            silence = np.zeros(int(self.sample_rate * self.silence_duration))

            for i, chunk in enumerate(chunks, 1):
                print(f"Processing chunk {i}/{len(chunks)}: {chunk[:50]}...")
                audio_chunk = self.process_chunk(chunk)
                audio_chunks.append(audio_chunk)
                audio_chunks.append(silence)

            # Combine and save
            combined_audio = np.concatenate(audio_chunks)
            wavfile.write(output_file, self.sample_rate, combined_audio)
            print(f"Audio saved to '{output_file}'")

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise

def main():
    """Main entry point of the application."""
    model_dir = "/Users/dolcera/Documents/email/demo/nix-tts/nix-ljspeech-deterministic-v0.1"
    converter = TextToSpeechConverter(model_dir)
    converter.convert('input.txt', 'output.wav')

if __name__ == "__main__":
    main()