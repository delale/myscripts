#!/Users/aledel/miniconda3/envs/soundprocessing/bin python
"""Automatic audio processing model to produced forced-aligned Praat TextGrids using Whiisper and Montreal-forced-aligner

1. transcribe audio files in a directory using openai-whisper
2. force-align using montreal-forced-aligner

Written for MacOS -> no GPU acceleration on openai-whisper 1.1.10 and montreal-forced-aligner 2.2.17

Usage:
    python3 auto-transcalign.py <path_to_corpus> <**optional arguments>

Example:
    # Transcribing and aligning audio files using Whisper and MFA (english and using large-v2 model)
    python3 auto-transcalign.py /path/to/corpus --output_path /path/to/output --language en --model large-v2

    # Transcribing and aligning audio files using only Whisper (+ word segmentation) (english and using base model)
    python3 auto-transcalign.py /path/to/corpus --output_path /path/to/output --whisper_align True --word_segmentation True --language en --model base

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


def transcribe_audio(
    path_to_corpus: str, language=None, model="large-v2", overwrite=False, logger=None
) -> None:
    """Transcribe audio using Whisper and the large-v2 model.

    Args:
        path_to_corpus: Path to the corpus.
        language: Language of the corpus. If None, automatically detected by Whisper (default=None).
        model: Name of Whisper model to use (default='large-v2').
        overwrite: Overwrite transcriptions if they are present (default=False).
        logger: Logger object (default=None).
    """
    if logger is None:
        logger = logging.getLogger(
            os.path.join(path_to_corpus, "../auto-transcalign.log")
        )

    # get all files in input directory
    audio_files = os.listdir(path_to_corpus)

    logger.info(f"Whisper on {path_to_corpus} corpus.")
    if language is None:
        logger.info(
            f"Whisper CMD: whisper "
            + f"{os.path.join(path_to_corpus, '<audio_file>')} "
            + f"--model {model} --output_format txt --verbose False "
            + f"--output_dir {path_to_corpus} --fp16 False"
        )
    else:
        logger.info(
            f"Whisper CMD: whisper "
            + f"{os.path.join(path_to_corpus, '<audio_file>')} "
            + f"--model {model} --output_format txt --verbose False "
            + f"--output_dir {path_to_corpus} --fp16 False --language {language}"
        )

    naudio = 0
    # For each audio file run Whisper transcription
    for audio in audio_files:
        # tested this only with WAV files so far
        if audio.endswith(".wav") or audio.endswith(".flac") or audio.endswith(".mp3"):
            naudio += 1
            # if overwrite is True or if the transcription does not exist
            if overwrite or os.path.splitext(audio)[0] + ".txt" not in audio_files:
                logger.info(f"Transcribing {audio}")
                whisper_cmd = (
                    f"whisper {os.path.join(path_to_corpus, audio)} "
                    + f"--model {model} --output_format txt --verbose False "
                    + f"--output_dir {path_to_corpus} --fp16 False"
                )
                if language is not None:
                    whisper_cmd += f" --language {language}"
                try:
                    subprocess.run(whisper_cmd.split())
                except Exception as e:
                    logger.error(f"{e}")
                    raise
            else:
                logger.info(f"Overwrite: {overwrite}; {audio} already transcribed.")

    logger.info(f"Transcribed {naudio} audio files.")
    return None


def align_audio(
    path_to_corpus: str,
    output_path=None,
    speaker_characters=None,
    dictionary="english_us_mfa",
    acoustic_model="english_mfa",
    clean=False,
    beam=100,
    retry_beam=400,
    include_original_text=True,
    textgrid_cleanup=True,
    num_jobs=3,
    logger=None,
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
        logger: Logger object (default=None).
    """
    if logger is None:
        logger = logging.getLogger(
            os.path.join(path_to_corpus, "../auto-transcalign.log")
        )

    if output_path is None:
        output_path = path_to_corpus
    elif not os.path.exists(output_path):
        os.makedirs(output_path)

    # Create mfa command
    if speaker_characters:
        mfa_cmd = (
            f"mfa align --speaker_characters "
            + f"{speaker_characters} {path_to_corpus} "
            + f"{dictionary} {acoustic_model} {output_path} "
            + f"--beam {beam} --retry_beam {retry_beam} --num_jobs {num_jobs}"
        )
    else:
        mfa_cmd = (
            f"mfa align {path_to_corpus} "
            + f"{dictionary} {acoustic_model} {output_path} "
            + f"--beam {beam} --retry_beam {retry_beam} --num_jobs {num_jobs}"
        )

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

    # Run mfa commandi
    logger.info(f"MFA on {path_to_corpus} corpus; output in {output_path}")
    logger.info(f"Running MFA command: {mfa_cmd}")
    try:
        subprocess.run(mfa_cmd.split())
    except Exception as e:
        logger.error(f"{e}")
        raise
    return None


def _make_textgrid_from_transcription(
    transcription: dict, duration: float, include_original_text: bool = False
) -> parselmouth.TextGrid:
    """Makes TextGrid from Whisper transcription."""
    if include_original_text:
        tier_names = ["text", "segments"]
    else:
        tier_names = ["segments"]
    if "words" in transcription["segments"][0]:
        tier_names.append("words")
    tg = parselmouth.TextGrid(start_time=0.0, end_time=duration, tier_names=tier_names)

    # Add boundaries and labels to the TextGrid
    if include_original_text:
        praat.call(tg, "Set interval text", 1, 1, transcription["text"])  # text tier
    segment_tier_num = 2 if include_original_text else 1
    if "words" in transcription["segments"][0]:
        words_tier_num = 3 if include_original_text else 2

    j = 0
    i = 0
    same_boundary_segment = 0
    same_boundary_segment_word = 0
    for ii, segment in enumerate(transcription["segments"]):
        # segments tier
        # add boundaries
        interval_num = i + 1
        if not segment["end"] >= duration and not (segment["end"] == segment["start"]):
            same_boundary_segment = 0
            praat.call(tg, "Insert boundary", segment_tier_num, segment["end"])

        if segment["end"] == segment["start"] and ii > 0:
            interval_num -= 1
            same_boundary_segment += 1
            praat.call(
                tg,
                "Set interval text",
                segment_tier_num,
                interval_num,
                " ".join(
                    [
                        transcription["segments"][x]["text"]
                        for x in range(ii - same_boundary_segment, ii)
                    ]
                )
                + segment["text"],
            )
        else:
            if segment["end"] == segment["start"] and ii == 0:
                praat.call(
                    tg, "Insert boundary", segment_tier_num, segment["end"] + 0.001
                )

            # add label
            praat.call(
                tg, "Set interval text", segment_tier_num, interval_num, segment["text"]
            )
            i += 1

        if "words" in segment:
            for jj, word in enumerate(segment["words"]):
                interval_num = j + 1
                if not word["end"] >= duration and not (word["end"] == word["start"]):
                    same_boundary_segment_word = 0
                    praat.call(tg, "Insert boundary", words_tier_num, word["end"])

                if word["end"] == word["start"] and jj > 0:
                    interval_num -= 1
                    same_boundary_segment_word += 1
                    praat.call(
                        tg,
                        "Set interval text",
                        words_tier_num,
                        interval_num,
                        " ".join(
                            [
                                segment["words"][x]["word"]
                                for x in range(jj - same_boundary_segment_word, jj)
                            ]
                        )
                        + word["word"],
                    )
                else:
                    if word["end"] == word["start"] and jj == 0:
                        praat.call(
                            tg, "Insert boundary", words_tier_num, word["end"] + 0.001
                        )
                    # add label
                    praat.call(
                        tg,
                        "Set interval text",
                        words_tier_num,
                        interval_num,
                        word["word"],
                    )
                    j += 1

    return tg


def textgrid_from_transcription(
    transcription: dict,
    duration: float,
    segment_level: bool = False,
    word_level: bool = False,
) -> parselmouth.TextGrid:
    """Creates Praat TextGrid from transcription.

    Parameters
    ----------
    transcription : dict
        Transcription dictionary including the following keys:
            "text": full transcription.
            "segments": (if `segment_level`) segment level transcriptions (e.g. sentences).
            "segments"["words"]: (if `word_level`) word level transcriptions.
        Caveats:
            - "segments" and "words" must be dictionaries with also "start" and "end" keys.
            - "words" is a dictionary in the "segments" dictionary.
        This dictionary follows the output structure of OpeanAI-Whisper.
    duration : float
        Audio file duration.
    segment_level : bool
        Include segment level transcriptions. Default is False.
    word_level : bool
        Include word level transcriptions. Default is False.

    Returns
    -------
    parselmouth.TextGrid
        TextGrid containing transcription (also segment level and word level if specified).
    """
    # Init tier names
    if not isinstance(transcription, dict):
        raise ValueError("`transcription` must be of type dict.")
    if "text" not in transcription:
        raise ValueError("'text' not found in `transcription`.")
    tier_names: list = ["text"]
    if segment_level:
        if "segments" not in transcription:
            logging.warning(
                "No segment level transcription found but segment_level is True: unable to add 'segments' tier to TextGrid."
            )
            segment_level = False
        else:
            tier_names.append("segments")
    if word_level:
        if "words" not in transcription["segments"][0]:
            logging.warning(
                "No word level transcription found but word_level is True: unable to add 'words' tier to TextGrid."
            )
            word_level = False
        else:
            tier_names.append("words")

    # Init TextGrid
    tg = parselmouth.TextGrid(
        start_time=0.0,
        end_time=duration,
        tier_names=tier_names,
    )

    # Add `text`
    praat.call(
        tg,
        "Set interval text",
        1,
        1,
        transcription["text"],
    )

    # Set appropriate tier numbers
    word_ntier = 3 if segment_level else 2

    # Add segment level
    if segment_level or word_level:
        i, j = 0, 0
        same_boundary_seg = 0
        same_boundary_word = 0

        # Loop through segments
        for ii, segment in enumerate(transcription["segments"]):
            # Segment level
            if segment_level:
                interval_num = i + 1
                t0 = segment["start"]
                t1 = segment["end"]

                # Add segment if not same boundary
                if not t1 >= duration and not t0 == t1:
                    same_boundary_seg = 0
                    praat.call(tg, "Insert boundary", 2, t1)
                    text = segment["text"]
                elif t0 == t1 and ii > 0:
                    # Adding to "prev" boundary
                    interval_num -= 1
                    same_boundary_seg += 1
                    text = " ".join(
                        [
                            transcription["segments"][x]["text"]
                            for x in range(ii - same_boundary_seg, ii)
                        ]
                    )
                    +segment["text"]
                elif t0 == t1 and ii == 0:
                    praat.call(
                        tg,
                        "Insert boundary",
                        2,
                        t1 + 0.001,
                    )
                    text = segment["text"]

                # Add text
                praat.call(
                    tg,
                    "Set interval text",
                    2,
                    interval_num,
                    text,
                )
                i += 1

            # Word level
            if word_level:
                for jj, word in enumerate(segment["words"]):
                    interval_num = j + 1
                    t0 = word["start"]
                    t1 = word["end"]

                    # Add word if not same boundary
                    if not t1 >= duration and not t0 == t1:
                        same_boundary_word = 0
                        praat.call(tg, "Insert boundary", word_ntier, t1)
                        text = word["word"]
                    elif t0 == t1 and jj > 0:
                        # Adding to "prev" boundary
                        interval_num -= 1
                        same_boundary_word += 1
                        text = " ".join(
                            [
                                segment["words"][x]["word"]
                                for x in range(ii - same_boundary_word, jj)
                            ]
                        )
                        +segment["text"]
                    elif t0 == t1 and jj == 0:
                        praat.call(
                            tg,
                            "Insert boundary",
                            word_ntier,
                            t1 + 0.001,
                        )
                        text = segment["word"]

                    # Add text
                    praat.call(
                        tg,
                        "Set interval text",
                        word_ntier,
                        interval_num,
                        text,
                    )
                    j += 1

    return tg


def whisper_transcribe_align(
    path_to_corpus: str,
    language: str = None,
    model: str = "large-v2",
    word_segmentation: bool = False,
    output_path: str = None,
    overwrite=False,
    include_original_text: bool = False,
    logger: logging.Logger = None,
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
        include_original_text: Include original utterance text in the output (default=False).
        logger: Logger object (default=None).
    """
    if logger is None:
        logger = logging.getLogger(
            os.path.join(path_to_corpus, "../auto-transcalign.log")
        )

    logger.info(f"Selected Whisper-Align opt on {path_to_corpus} corpus.")
    # get all files in input directory
    audio_files = os.listdir(path_to_corpus)
    model = whisper.load_model(model)  #  load whisper model

    if output_path is None:
        output_path = path_to_corpus
    elif not os.path.exists(output_path):
        os.makedirs(output_path)

    logger.info(f"Processing {len(audio_files)} files...")
    naudio = 0
    for audio in audio_files:
        if audio.endswith(".wav") or audio.endswith(".flac") or audio.endswith(".mp3"):
            naudio += 1
            # if overwrite is True or if the transcription does not exist
            if overwrite or os.path.splitext(audio)[0] + ".TextGrid" not in audio_files:
                logger.info(f"Transcribing {audio}")
                # copy to output path
                if output_path != path_to_corpus:
                    sh.copy(os.path.join(path_to_corpus, audio), output_path)
                # transcribe
                signal = whisper.audio.load_audio(os.path.join(path_to_corpus, audio))
                transcription = model.transcribe(
                    signal, word_timestamps=word_segmentation, language=language
                )

                # save transcription
                dur = len(signal) / 16000  # default sample rate
                # tg = _make_textgrid_from_transcription(
                #     transcription, dur, include_original_text
                # )
                tg = textgrid_from_transcription(
                    transcription,
                    dur,
                    segment_level=True,
                    word_level=True,
                )
                tg.save(
                    os.path.join(output_path, os.path.splitext(audio)[0] + ".TextGrid")
                )
            else:
                logger.info(f"Overwrite: {overwrite}; {audio} already transcribed.")

    logger.info(f"Transcribed {naudio} audio files; output in {output_path}.")
    return None


def main():
    # init parser
    parser = argparse.ArgumentParser(
        prog="auto-transcalign",
        description="""Transcribe and force-align audio using Whisper and Montreal-Forced-Aligner.
        
        Usage: python3 auto-transcalign.py <path_to_corpus> <**optional arguments>
        
        The program was built for MacOS (no GPU acceleration on openai-whisper 1.1.10 and montral-forced-aligner 2.2.17).
        Alessandro De Luca - alessandro.deluca@uzh.ch - 10-2023.""",
    )
    parser.add_argument(
        "path_to_corpus", help="Path to the corpus containing the audio files."
    )
    parser.add_argument(
        "--whisper_align",
        help="Use Whisper for transcription and alignment. Default is False.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )  # if True, use Whisper for transcription and alignment

    whisper_arguments = [
        {
            "name": "--language",
            "help": "[Whisper arg] Language of the corpus. If None, automatically detected by Whisper (default=None).",
            "default": None,
            "type": str,
        },
        {
            "name": "--model",
            "help": "[Whisper arg] Name of Whisper model to use (default='large-v2').",
            "default": "large-v2",
            "type": str,
        },
        {
            "name": "--overwrite",
            "help": "[Whisper arg] Overwrite transcriptions if they are present (default=False)",
            "default": False,
            "action": argparse.BooleanOptionalAction,
        },
    ]

    mfa_arguments = [
        {
            "name": "--output_path",
            "help": "[MFA arg] Path to the output directory. If None, path_to_corpus is used (default=None).",
            "default": None,
            "type": str,
        },
        {
            "name": "--speaker_characters",
            "help": "[MFA arg] Number of characters of file names to use for determining speaker (default=None).",
            "default": None,
            "type": int,
        },
        {
            "name": "--dictionary",
            "help": "[MFA arg] Name or path of the pronounciation dictionary (default=english_us_mfa).",
            "default": "english_us_mfa",
            "type": str,
        },
        {
            "name": "--acoustic_model",
            "help": "[MFA arg] Name or path of the pretrained acoustic model (default=english_mfa).",
            "default": "english_mfa",
            "type": str,
        },
        {
            "name": "--clean",
            "help": "[MFA arg] Remove files from previous runs (default=False).",
            "default": False,
            "action": argparse.BooleanOptionalAction,
        },
        {
            "name": "--beam",
            "help": "[MFA arg] Beam size (default=100).",
            "default": 100,
            "type": int,
        },
        {
            "name": "--retry_beam",
            "help": "[MFA arg] Rerun beam size (default=400).",
            "default": 400,
            "type": int,
        },
        {
            "name": "--include_original_text",
            "help": "Include original utterance text in the output (default=True).",
            "default": True,
            "action": argparse.BooleanOptionalAction,
        },
        {
            "name": "--textgrid_cleanup",
            "help": "[MFA arg] Post-processing of TextGrids that cleans up silences and recombines compound words and clitics (default=True).",
            "default": True,
            "action": argparse.BooleanOptionalAction,
        },
        {
            "name": "--num_jobs",
            "help": "[MFA arg] Set the number of processes to use (default=3).",
            "default": 3,
            "type": int,
        },
    ]

    whisper_align_arguments = [
        {
            "name": "--word_segmentation",
            "help": "[Whisper-Align arg] Perform word-level segmentation (default=False).",
            "default": False,
            "action": argparse.BooleanOptionalAction,
        }
    ]
    # add args to parser
    for arg_info in whisper_arguments:
        kwargs = arg_info.copy()
        name = kwargs.pop("name")
        parser.add_argument(name, **kwargs)
    for arg_info in mfa_arguments:
        kwargs = arg_info.copy()
        name = kwargs.pop("name")
        parser.add_argument(name, **kwargs)
    for arg_info in whisper_align_arguments:
        kwargs = arg_info.copy()
        name = kwargs.pop("name")
        parser.add_argument(name, **kwargs)

    args = parser.parse_args()
    path_to_corpus = args.path_to_corpus

    # extract whisper args
    whisper_args = {
        arg: (
            getattr(args, arg)[0]
            if isinstance(getattr(args, arg), list)
            else getattr(args, arg)
        )
        for arg in [
            arg_info["name"].replace("--", "") for arg_info in whisper_arguments
        ]
    }

    # extract mfa args
    mfa_args = {
        arg: (
            getattr(args, arg)[0]
            if isinstance(getattr(args, arg), list)
            else getattr(args, arg)
        )
        for arg in [arg_info["name"].replace("--", "") for arg_info in mfa_arguments]
    }

    # extract whisper-align args
    whisper_align_args = {
        arg: (
            getattr(args, arg)[0]
            if isinstance(getattr(args, arg), list)
            else getattr(args, arg)
        )
        for arg in [
            arg_info["name"].replace("--", "") for arg_info in whisper_align_arguments
        ]
    }

    # Setup logging
    if mfa_args["output_path"] is None:
        logging.basicConfig(
            filename=os.path.join(path_to_corpus, "../auto-transcalign.log"),
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logger = logging.getLogger(
            os.path.join(path_to_corpus, "../auto-transcalign.log")
        )
    else:
        if not os.path.exists(mfa_args["output_path"]):
            os.makedirs(mfa_args["output_path"])
        logging.basicConfig(
            filename=os.path.join(mfa_args["output_path"], "auto-transcalign.log"),
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logger = logging.getLogger(
            os.path.join(mfa_args["output_path"], "auto-transcalign.log")
        )

    if not args.whisper_align:
        # Transcribe audio
        transcribe_audio(path_to_corpus=path_to_corpus, logger=logger, **whisper_args)
        logger.info("Finished transcription!\n\n")

        # Align audio
        align_audio(path_to_corpus=path_to_corpus, logger=logger, **mfa_args)
        logger.info("Finished alignment.")
    else:
        whisper_transcribe_align(
            path_to_corpus=path_to_corpus,
            output_path=mfa_args["output_path"],
            include_original_text=mfa_args["include_original_text"],
            logger=logger,
            **whisper_args,
            **whisper_align_args,
        )
        logger.info("Finished Whisper-Align transcription and alignment.")


if __name__ == "__main__":
    main()
