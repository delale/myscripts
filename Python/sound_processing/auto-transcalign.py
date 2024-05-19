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
import logging
import shutil as sh
import subprocess
import whisper
import parselmouth
from parselmouth import praat


def transcribe_audio(path_to_corpus: str, language=None, model="large-v2", overwrite=False) -> None:
    """Transcribe audio using Whisper and the large-v2 model.

    Args:
        path_to_corpus: Path to the corpus.
        language: Language of the corpus. If None, automatically detected by Whisper (default=None).
        model: Name of Whisper model to use (default='large-v2').
        overwrite: Overwrite transcriptions if they are present (default=False).
    """
    logger = logging.getLogger(os.path.join(
        path_to_corpus, "../auto-transcalign.log"))
    audio_files = os.listdir(
        path_to_corpus)    # get all files in input directory

    logger.info(f"Whisper on {path_to_corpus} corpus.")
    if language is None:
        logger.info(
            f"Whisper CMD: whisper {os.path.join(path_to_corpus, '<audio_file>')} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False")
    else:
        logger.info(
            f"Whisper CMD: whisper {os.path.join(path_to_corpus, '<audio_file>')} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False --language {language}")

    naudio = 0
    # For each audio file run Whisper transcription
    for audio in audio_files:
        # tested this only with WAV files so far
        if audio.endswith(".wav") or audio.endswith(".flac") or audio.endswith(".mp3"):
            naudio += 1
            # if overwrite is True or if the transcription does not exist
            if overwrite or os.path.splitext(audio)[0]+".txt" not in audio_files:
                logger.info(f"Transcribing {audio}")
                whisper_cmd = f"whisper {os.path.join(path_to_corpus, audio)} --model {model} --output_format txt --verbose False --output_dir {path_to_corpus} --fp16 False"
                if language is not None:
                    whisper_cmd += f" --language {language}"
                try:
                    subprocess.run(whisper_cmd.split())
                except Exception as e:
                    logger.error(f"{e}")
                    raise
            else:
                logger.info(
                    f"Overwrite: {overwrite}; {audio} already transcribed.")

    logger.info(f"Transcribed {naudio} audio files.")
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
    logger = logging.getLogger(os.path.join(
        path_to_corpus, "../auto-transcalign.log"))

    if output_path is None:
        output_path = path_to_corpus
    elif not os.path.exists(output_path):
        os.makedirs(output_path)

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
    logger.info(f"MFA on {path_to_corpus} corpus; output in {output_path}")
    logger.info(f"Running MFA command: {mfa_cmd}")
    try:
        subprocess.run(mfa_cmd.split())
    except Exception as e:
        logger.error(f"{e}")
        raise
    return None


def _make_textgrid_from_transcription(transcription: dict, duration: float) -> parselmouth.TextGrid:
    """Makes TextGrid from Whisper transcription."""
    tier_names = ['text', 'segments']
    if 'words' in transcription['segments'][0]:
        tier_names.append('words')
    tg = parselmouth.TextGrid(
        start_time=0.0, end_time=duration, tier_names=tier_names)

    # Add boundaries and labels to the TextGrid
    praat.call(tg, "Set interval text", 1, 1,
               transcription['text'])  # text tier
    j = 0
    for i, segment in enumerate(transcription['segments']):
        # segments tier
        # add boundaries
        interval_num = i + 1
        if not segment['end'] >= duration:
            praat.call(tg, "Insert boundary", 2, segment['end'])

        # add label
        praat.call(tg, "Set interval text", 2, interval_num, segment['text'])

        if 'words' in segment:
            for k, word in enumerate(segment['words']):
                interval_num = j + 1
                if not word['end'] >= duration:
                    praat.call(tg, "Insert boundary", 3, word['end'])

                # add label
                praat.call(tg, "Set interval text", 3,
                           interval_num, word['word'])
                j += 1

    return tg


def whisper_transcribe_align(
    path_to_corpus: str, language: str = None, model: str = "large-v2",
    word_segmentation: bool = False, output_path: str = None, overwrite=False
) -> None:
    """Function to transcribe audio and align it using purely Whisper to a TextGrid.
    Alignment is done at the segment or word (if word_segmentation = True) level.

    Args:
        path_to_corpus: Path to the corpus containing the audio files.
        language: Language of the corpus. If None, automatically detected by Whisper (default=None).
        model: Name of Whisper model to use (default='large-v2').
        word_segmentation: Perform word-level segmentation (default=False).
        output_path: Path to the output directory. If None, path_to_corpus is used (default=None).
        overwrite: Overwrite transcriptions if they are present (default=False).
    """
    logger = logging.getLogger(os.path.join(
        path_to_corpus, "../auto-transcalign.log"))
    audio_files = os.listdir(
        path_to_corpus)    # get all files in input directory

    logger.info(f"Selected Whisper-Align opt on {path_to_corpus} corpus.")

    model = whisper.load_model(model)

    if output_path is None:
        output_path = path_to_corpus
    elif not os.path.exists(output_path):
        os.makedirs(output_path)

    logger.info(f'Processing {len(audio_files)} files...')
    naudio = 0
    for audio in audio_files:
        if audio.endswith(".wav") or audio.endswith('.flac') or audio.endswith('.mp3'):
            naudio += 1
            # if overwrite is True or if the transcription does not exist
            if overwrite or os.path.splitext(audio)[0]+".TextGrid" not in audio_files:
                logger.info(f"Transcribing {audio}")
                # copy to output path
                if output_path != path_to_corpus:
                    sh.copy(os.path.join(path_to_corpus, audio), output_path)
                # transcribe
                signal = whisper.audio.load_audio(
                    os.path.join(path_to_corpus, audio))
                transcription = model.transcribe(
                    signal, word_timestamps=word_segmentation, language=language)

                # save transcription
                dur = len(signal) / 16000  # default sample rate
                tg = _make_textgrid_from_transcription(transcription, dur)
                tg.save(os.path.join(output_path,
                        os.path.splitext(audio)[0]+".TextGrid"))
            else:
                logger.info(
                    f'Overwrite: {overwrite}; {audio} already transcribed.')

    logger.info(f"Transcribed {naudio} audio files; output in {output_path}.")
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
    parser.add_argument(
        "--whisper_align", help="Use Whisper for transcription and alignment.", default=False, type=bool
    )   # if True, use Whisper for transcription and alignment

    whisper_arguments = [
        {'name': "language",
            'help': "[Whisper arg] Language of the corpus. If None, automatically detected by Whisper (default=None).", 'default': None, 'type': str},
        {'name': "model",
            'help': "[Whisper arg] Name of Whisper model to use (default='large-v2').", 'default': "large-v2", 'type': str},
        {'name': "overwrite",
            'help': "[Whisper arg] Overwrite transcriptions if they are present (default=False)", 'default': False, 'type': bool}
    ]

    mfa_arguments = [
        {'name': "output_path",
            'help': "[MFA arg] Path to the output directory. If None, path_to_corpus is used (default=None).", 'default': None, 'type': str},
        {'name': "speaker_characters",
            'help': "[MFA arg] Number of characters of file names to use for determining speaker (default=None).", 'default': None, 'type': int},
        {'name': "dictionary",
            'help': "[MFA arg] Name or path of the pronounciaton dictionary (default=english_us_mfa).", 'default': "english_us_mfa", 'type': str},
        {'name': "acoustic_model",
            'help': "[MFA arg] Name or path of the pretrained acoustic model (default=english_mfa).", 'default': "english_mfa", 'type': str},
        {'name': "clean",
            'help': "[MFA arg] Remove files from previous runs (default=False).", 'default': False, 'type': bool},
        {'name': "beam",
            'help': "[MFA arg] Beam size (default=100).", 'default': 100, 'type': int},
        {'name': "retry_beam",
            'help': "[MFA arg] Rerun beam size (default=400).", 'default': 400, 'type': int},
        {'name': "include_original_text",
            'help': "[MFA arg] Include original utterance text in the output (default=True).", 'default': True, 'type': bool},
        {'name': "textgrid_cleanup",
            'help': "[MFA arg] Post-processing of TextGrids that cleans up silences and recombines compound words and clitics (default=True).", 'default': True, 'type': bool},
        {'name': "num_jobs",
            'help': "[MFA arg] Set the number of processes to use (default=3).", 'default': 3, 'type': int}
    ]

    whisper_align_arguments = [
        {'name': 'word_segmentation',
            'help': '[Whisper-Align arg] Perform word-level segmentation (default=False).', 'default': False, 'type': bool},
    ]

    for arg_info in whisper_arguments:
        parser.add_argument(
            "--"+arg_info['name'], nargs="*", help=arg_info['help'], default=arg_info['default'], type=arg_info['type'])
    for arg_info in mfa_arguments:
        parser.add_argument(
            "--"+arg_info['name'], nargs="*", help=arg_info['help'], default=arg_info['default'], type=arg_info['type'])
    for arg_info in whisper_align_arguments:
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

    # extract whisper-align args
    whisper_align_args = {arg: getattr(args, arg)[0] if isinstance(getattr(args, arg), list) else getattr(args, arg) for arg in [
        arg_info['name'] for arg_info in whisper_align_arguments]}

    # Setup logging
    logging.basicConfig(
        filename=os.path.join(path_to_corpus, "../auto-transcalign.log"), level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(os.path.join(
        path_to_corpus, "../auto-transcalign.log"))

    if not args.whisper_align:
        # Transcribe audio
        transcribe_audio(path_to_corpus=path_to_corpus, **whisper_args)
        logger.info("Finished transcription!\n\n")

        # Align audio
        align_audio(path_to_corpus=path_to_corpus, **mfa_args)
        logger.info("Finished alignment.")
    else:
        whisper_transcribe_align(
            path_to_corpus=path_to_corpus, output_path=mfa_args['output_path'],
            **whisper_args, **whisper_align_args)
        logger.info("Finished Whisper-Align transcription and alignment.")


if __name__ == "__main__":
    main()
