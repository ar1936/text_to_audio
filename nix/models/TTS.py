"""
Nix Text-to-Speech Inference Module

This module provides the main inference functionality for the Nix TTS system,
handling text tokenization and audio generation using ONNX runtime models.
"""

import os
import pickle
from typing import Tuple, List, Optional

import numpy as np
import onnxruntime as ort

from nix.tokenizers.tokenizer_en import NixTokenizerEN

class NixTTSInference:
    """
    Text-to-Speech inference class that handles tokenization and audio generation.
    
    Attributes:
        tokenizer: English text tokenizer instance
        encoder: ONNX runtime session for the encoder model
        decoder: ONNX runtime session for the decoder model
    """

    def __init__(self, model_dir: str) -> None:
        """
        Initialize the TTS inference system.

        Args:
            model_dir: Directory containing the model files (tokenizer_state.pkl, 
                      encoder.onnx, decoder.onnx)

        Raises:
            FileNotFoundError: If model files are not found
            RuntimeError: If ONNX model loading fails
        """
        try:
            # Load tokenizer
            tokenizer_path = os.path.join(model_dir, "tokenizer_state.pkl")
            with open(tokenizer_path, "rb") as f:
                tokenizer_state = pickle.load(f)
            self.tokenizer = NixTokenizerEN(tokenizer_state)

            # Load TTS models
            encoder_path = os.path.join(model_dir, "encoder.onnx")
            decoder_path = os.path.join(model_dir, "decoder.onnx")
            
            if not all(os.path.exists(p) for p in [encoder_path, decoder_path]):
                raise FileNotFoundError("Model files not found in specified directory")

            self.encoder = ort.InferenceSession(encoder_path)
            self.decoder = ort.InferenceSession(decoder_path)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize TTS system: {str(e)}")

    def tokenize(self, text: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Tokenize input text into model-ready format.

        Args:
            text: Input text to tokenize

        Returns:
            Tuple containing:
                - Token arrays (np.int64)
                - Token lengths (np.int64)
                - Phoneme sequences

        Raises:
            ValueError: If input text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        # Tokenize input text
        c, c_lengths, phonemes = self.tokenizer([text])
        
        return (np.array(c, dtype=np.int64), 
                np.array(c_lengths, dtype=np.int64), 
                phonemes)

    def vocalize(self, c: np.ndarray, c_lengths: np.ndarray) -> np.ndarray:
        """
        Generate audio from tokenized input.

        Args:
            c: Token arrays from tokenizer
            c_lengths: Token lengths from tokenizer

        Returns:
            Generated audio waveform as numpy array

        Raises:
            RuntimeError: If inference fails
        """
        try:
            # Infer latent samples from encoder
            z = self.encoder.run(
                None,
                {
                    "c": c,
                    "c_lengths": c_lengths,
                }
            )[2]

            # Decode raw audio with decoder
            xw = self.decoder.run(
                None,
                {
                    "z": z,
                }
            )[0]

            return xw

        except Exception as e:
            raise RuntimeError(f"Audio generation failed: {str(e)}")