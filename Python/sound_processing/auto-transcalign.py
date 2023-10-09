#!/Users/aledel/miniconda3/envs/soundprocessing/bin python
"""Autpmatic audio processing model to produced forced-aligned Praat textgrids using whisper and montreal forced-aligner
  
1. transcribe audio files in a directory using whisper.cpp
2. force-align using montreal-forced-aligner

Author: Alessandro De Luca
Date: 10-2023
Contact: alessandro.deluca@uzh.ch
"""
import argparse
import os
import subprocess
import logging


def transcribe_audio(path_to_corpus: str, verbose=None):
    """Transcribe audio using Whisper and the large-v2 model.

    Args:
        path_to_corpus: Path to the corpus (containing all audio files).
        verbose: Verbosity level
    """
    audio_files = os.listdir(path_to_corpus)

    for audio in audio_files:
        whsiper_cmd = f"whisper {os.path.join(path_to_corpus, audio_files)} --model large-v2 --output-format txt --verbose False"


def main():
    logging.basicConfig(
        filename='auto-transcalign.log', level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger("auto-transcribe")
