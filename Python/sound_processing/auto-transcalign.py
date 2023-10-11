#!/Users/aledel/miniconda3/envs/soundprocessing/bin python
"""Automatic audio processing model to produced forced-aligned Praat TextGrids using Whiisper and Montreal-forced-aligner
  
1. transcribe audio files in a directory using openai-whisper
2. force-align using montreal-forced-aligner

Written for MacOS -> no GPU acceleration on openai-whisper 1.1.10 and montreal-forced-aligner 2.2.17

Usage:
    python3 auto-transcalign.py <path_to_corpus> <**optional arguments>

Author: Alessandro De Luca
Date: 10-2023
Contact: alessandro.deluca@uzh.ch
"""
import argparse
import os
import subprocess
import logging


def transcribe_audio(path_to_corpus: str, language=None, model="large-v2") -> None:
    """Transcribe audio using Whisper and the large-v2 model.

    Args:
        path_to_corpus: Path to the corpus.
        language: Language of the corpus. If None, automatically detected by Whisper (default=None).
        model = Name of Whisper model to use (default='large-v2').
    """
    audio_files = os.listdir(
        path_to_corpus)    # get all files in input directory

    logging.info(f"Whisper on {path_to_corpus} corpus.")
    if language is None:
        logging.info(
            f"Whisper CMD: whisper {os.path.join(path_to_corpus, '<audio_file>')} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False")
    else:
        logging.info(
            f"Whisper CMD: whisper {os.path.join(path_to_corpus, '<audio_file>')} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False --language {language}")

    # For each audio file run Whisper transcription
    for audio in audio_files:
        # tested this only with WAV files so far
        if audio.endswith(".wav") or audio.endswith(".flac") or audio.endswith(".mp3"):
            logging.info(f"Transcribing {audio}")
            whisper_cmd = f"whisper {os.path.join(path_to_corpus, audio)} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False"
            if language is not None:
                whisper_cmd += f" --language {language}"
            try:
                subprocess.run(whisper_cmd.split())
            except Exception as e:
                logging.error(f"{e}")
                raise
    return None


def align_audio(
        path_to_corpus: str, output_path=None, speaker_characters=None,
        dictionary="english_us_mfa", acoustic_model="english_mfa", clean=False,
        beam=100, retry_beam=400, include_original_text=True,
        textgrid_cleanup=True, num_jobs=3
) -> None:
    """Force-aligns all audio files in the corpus using MFA.

    Args:
        path_to_corpus: Path to the corpus.
        output_path: Path to output directory. If None, path_to_corpus is used (default=None).
        speaker_characters: Number of characters of file names to use for determening speaker (default=None).
        dictionary: Name or path of the pronounciation dictionary (default='english_us_mfa').
        acoustic_model: Name or path of the pretrained acoustic model (default='english_mfa').
        clean: Remove files from previous runs (default=False).
        beam: Beam size (default=100).
        retry_beam: Rerun beam size (default=400).
        include_original_text: Include original utterance text in the output (default=True).
        textgrid_cleanup: Post-processing of TextGrids that cleans up silences and recombines compound words and clitics (default=True).
        num_jobs: Set the number of processes to use (default=3).
    """
    if output_path is None:
        output_path = path_to_corpus

    # Create mfa command
    if speaker_characters:
        mfa_cmd = f"mfa align --speaker_characters {speaker_characters} {path_to_corpus} {dictionary} {acoustic_model} {output_path} --beam {beam} --retry_beam {retry_beam} --num_jobs {num_jobs}"
    else:
        mfa_cmd = f"mfa align {path_to_corpus} {dictionary} {acoustic_model} {output_path} --beam {beam} --retry_beam {retry_beam} --num_jobs {num_jobs}"

    if clean:
        mfa_cmd += " --clean"
    else:
        mfa_cmd += " --no_clean"

    if include_original_text:
        mfa_cmd += " --include_original_text"

    if textgrid_cleanup:
        mfa_cmd += " --textgrid_cleanup"
    else:
        mfa_cmd += " --no_textgrid_cleanup"

    # Run mfa command
    logging.info(f"MFA on {path_to_corpus} corpus; output in {output_path}")
    logging.info(f"Running MFA command: {mfa_cmd}")
    try:
        subprocess.run(mfa_cmd.split())
    except Exception as e:
        logging.error(f"{e}")
        raise
    return None


def main():
    # init parser
    parser = argparse.ArgumentParser(
        prog="auto-transcalign",
        description="""Transcribe and force-align audio using Whisper and Montreal-Forced-Aligner.
        
        Usage: python3 auto-transcalign.py <path_to_corpus> <**optional arguments>
        
        The program was built for MacOS (no GPU acceleration on openai-whisper 1.1.10 and montral-forced-aligner 2.2.17).
        Alessandro De Luca - alessandro.deluca@uzh.ch - 10-2023."""
    )
    parser.add_argument(
        "path_to_corpus", help="Path to the corpus containing the audio files."
    )

    whisper_arguments = [
        {'name': "language",
            'help': "Language of the corpus. If None, automatically detected by Whisper (default=None).", 'default': None, 'type': str},
        {'name': "model",
            'help': "Name of Whisper model to use (default='large-v2').", 'default': "large-v2", 'type': str}
    ]

    mfa_arguments = [
        {'name': "output_path",
            'help': "Path to the output directory. If None, path_to_corpus is used (default=None).", 'default': None, 'type': str},
        {'name': "speaker_characters",
            'help': "Number of characters of file names to use for determining speaker (default=None).", 'default': None, 'type': int},
        {'name': "dictionary",
            'help': "Name or path of the pronounciaton dictionary (default=english_us_mfa).", 'default': "english_us_mfa", 'type': str},
        {'name': "acoustic_model",
            'help': "Name or path of the pretrained acoustic model (default=english_mfa).", 'default': "english_mfa", 'type': str},
        {'name': "clean",
            'help': "Remove files from previous runs (default=False).", 'default': False, 'type': bool},
        {'name': "beam",
            'help': "Beam size (default=100).", 'default': 100, 'type': int},
        {'name': "retry_beam",
            'help': "Rerun beam size (default=400).", 'default': 400, 'type': int},
        {'name': "include_original_text",
            'help': "Include original utterance text in the output (default=True).", 'default': True, 'type': bool},
        {'name': "textgrid_cleanup",
            'help': "Post-processing of TextGrids that cleans up silences and recombines compound words and clitics (default=True).", 'default': True, 'type': bool},
        {'name': "num_jobs",
            'help': "Set the number of processes to use (default=3).", 'default': 3, 'type': int}
    ]

    for arg_info in whisper_arguments:
        parser.add_argument(
            "--"+arg_info['name'], nargs="*", help=arg_info['help'], default=arg_info['default'], type=arg_info['type'])
    for arg_info in mfa_arguments:
        parser.add_argument(
            "--"+arg_info['name'], nargs="*", help=arg_info['help'], default=arg_info['default'], type=arg_info['type'])

    args = parser.parse_args()
    path_to_corpus = args.path_to_corpus

    # extract whisper args
    whisper_args = {arg: getattr(args, arg)[0] if isinstance(getattr(args, arg), list) else getattr(args, arg) for arg in [
        arg_info['name'] for arg_info in whisper_arguments]}

    # extract mfa args
    mfa_args = {arg: getattr(args, arg)[0] if isinstance(getattr(args, arg), list) else getattr(args, arg) for arg in [
        arg_info['name'] for arg_info in mfa_arguments]}

    # Setup logging
    logging.basicConfig(
        filename=os.path.join(path_to_corpus, "../auto-transcalign.log"), level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger("auto-transcribe")

    # Transcribe audio
    transcribe_audio(path_to_corpus=path_to_corpus, **whisper_args)
    logging.info("Finished transcription!\n\n")

    # Align audio
    align_audio(path_to_corpus=path_to_corpus, **mfa_args)


if __name__ == "__main__":
    main()
