"""
English Text Tokenizer for Nix-TTS

This module provides tokenization functionality for English text, converting it into
phonemes and preparing it for text-to-speech processing. It handles abbreviation expansion,
phoneme generation, and token padding.

Dependencies:
    - phonemizer: For converting text to phonemes
    - re: For regular expression operations
"""

import re
from phonemizer.backend import EspeakBackend
from typing import List, Tuple, Dict, Any

class NixTokenizerEN:
    """
    English text tokenizer that converts text into phonemes and prepares tokens for TTS processing.
    
    Attributes:
        vocab_dict (Dict): Dictionary mapping phonemes to their corresponding token IDs
        abbreviations_dict (Dict): Dictionary of abbreviations and their expansions
        whitespace_regex (str): Regular expression pattern for handling whitespace
        abbreviations_regex (List[Tuple]): List of (regex, replacement) pairs for abbreviations
    """

    def __init__(self, tokenizer_state: Dict[str, Any]) -> None:
        """
        Initialize the tokenizer with the given state.

        Args:
            tokenizer_state: Dictionary containing tokenizer configuration:
                - vocab_dict: Phoneme to token ID mapping
                - abbreviations_dict: Abbreviation expansions
                - whitespace_regex: Whitespace handling pattern
                - abbreviations_regex: Abbreviation replacement patterns
        """
        self.vocab_dict = tokenizer_state["vocab_dict"]
        self.abbreviations_dict = tokenizer_state["abbreviations_dict"]
        self.whitespace_regex = tokenizer_state["whitespace_regex"]
        self.abbreviations_regex = tokenizer_state["abbreviations_regex"]
        
        # Initialize phonemizer backend
        self.phonemizer = EspeakBackend(
            language='en-us',
            preserve_punctuation=True,
            with_stress=True
        )

    def __call__(self, texts: List[str]) -> Tuple[List[List[int]], List[int], List[str]]:
        """
        Convert input texts to phoneme tokens.

        Args:
            texts: List of input texts to tokenize

        Returns:
            Tuple containing:
                - tokens: Padded token sequences
                - tokens_lengths: Length of each token sequence
                - phonemes: Generated phoneme sequences
        """
        # Generate phonemes from input texts
        phonemes = [
            self._collapse_whitespace(
                self.phonemizer.phonemize(
                    self._expand_abbreviations(text.lower()),
                    strip=True
                )
            ) for text in texts
        ]

        # Convert phonemes to token sequences
        tokens = [
            self._intersperse(
                [self.vocab_dict[p] for p in phoneme],
                0  # Padding token
            ) for phoneme in phonemes
        ]

        # Pad token sequences to equal length
        tokens, tokens_lengths = self._pad_tokens(tokens)

        return tokens, tokens_lengths, phonemes

    def _expand_abbreviations(self, text: str) -> str:
        """
        Expand abbreviations in the input text using regex patterns.

        Args:
            text: Input text containing abbreviations

        Returns:
            Text with expanded abbreviations
        """
        for regex, replacement in self.abbreviations_regex:
            text = re.sub(regex, replacement, text)
        return text

    def _collapse_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text using defined regex pattern.

        Args:
            text: Input text with potentially irregular whitespace

        Returns:
            Text with normalized whitespace
        """
        return re.sub(self.whitespace_regex, ' ', text)

    def _intersperse(self, lst: List[int], item: int) -> List[int]:
        """
        Insert an item between each element of the list.

        Args:
            lst: Input list of tokens
            item: Item to insert between tokens

        Returns:
            List with item inserted between original elements
        """
        result = [item] * (len(lst) * 2 + 1)
        result[1::2] = lst
        return result

    def _pad_tokens(self, tokens: List[List[int]]) -> Tuple[List[List[int]], List[int]]:
        """
        Pad token sequences to the length of the longest sequence.

        Args:
            tokens: List of token sequences

        Returns:
            Tuple containing:
                - Padded token sequences
                - Original lengths of sequences
        """
        tokens_lengths = [len(token) for token in tokens]
        max_len = max(tokens_lengths)
        tokens = [token + [0] * (max_len - len(token)) for token in tokens]
        return tokens, tokens_lengths