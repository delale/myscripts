"""Script to detect the language of a given recording using the OpenAI Whisper.

Requirements:
- python >= 3.10
- openai-whisper = 20231117
- torch = 2.3.1

Usage:
python3 whisper_language_detection.py <audio_file_path> --model_id <model_id> --output_path <output_path> --max_analysis_length <max_analysis_length>

The script may be slow to run at first if you don't have the whisper model downloaded 
yet locally.
"""

import argparse
from collections import defaultdict
import datetime
import logging
import math
import os
import torch
import whisper
from whisper.audio import log_mel_spectrogram, load_audio, N_FRAMES
from whisper.tokenizer import LANGUAGES

MAX_ANALYSIS_LENGTH = 1920000  # equivalent to 120 seconds of audio (16kHz * 120)
EXTENSIONS = [".wav", ".mp3", ".flac"]

now = datetime.datetime.now()

# init logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"whisper_language_detection_{now.strftime('%Y-%m-%d_%H.%M')}.log", mode="w"
        ),
    ],
)


def detect_language(
    audio_path: str,
    whisper_model: whisper.model.Whisper,
    max_analysis_length: int = 1920000,
) -> tuple[str, float, dict]:
    """Detect the language of the given audio file using the OpenAI Whisper model.

    Parameters:
    ------------
    audio_path: str
        The path to the audio file to detect the language of.
    whisper_model: whisper.model.Whisper
        The whisper model to use for language detection.
    max_analysis_length: int
        The maximum number of frames to analyze. Default is 120 seconds of audio (16kHz * 120).

    Returns:
    --------
    str
        The detected language of the audio file.
    float
        The probability of the detected language.
    dict
        A dictionary of all the languages and their probabilities.
    """
    if not whisper_model.is_multilingual:
        raise ValueError("Whisper model is not multilingual.")

    signal = load_audio(audio_path)  # load audio file

    # get log mel spectrogram
    log_mel = log_mel_spectrogram(signal, whisper_model.dims.n_mels)

    # get number of frames
    n_frames = log_mel.shape[-1]

    # check if file is shorter than the minimum analysis length
    if n_frames < N_FRAMES:
        logging.warning(f"Audio file shorter than mimimum analysis length -> padding")
        pad_widths = [(0, 0)] * log_mel.ndim
        pad_widths[-1] = (0, N_FRAMES - n_frames)
        log_mel = torch.nn.functional.pad(
            log_mel, [pad for sizes in pad_widths[::-1] for pad in sizes]
        )
        n_frames = log_mel.shape[-1]

    # Loop through the audio file in chunks of N_FRAMES until max_analysis_length
    logging.info("Detecting language...")
    j = 1  # frame counter
    lang_probs = defaultdict(float)
    for i in range(0, min(n_frames, max_analysis_length), N_FRAMES):
        end_frame = min(i + N_FRAMES, n_frames)
        analysis_frame = log_mel.index_select(
            dim=-1, index=torch.arange(i, end_frame, device=log_mel.device)
        )
        # langugae detection
        _, probs = whisper_model.detect_language(analysis_frame)

        logging.info(
            f"Highest probability for analysis frame {j}: {LANGUAGES[max(probs, key=probs.get)].title()}"
        )
        j += 1

        # update language probabilities
        for lang, prob in probs.items():
            lang_probs[lang] += math.log(prob)

    logging.info("Language detection complete.")
    # get the language with the highest probability
    detect_language = max(lang_probs, key=lang_probs.get)
    max_prob = math.exp(lang_probs[detect_language])
    all_probs = {
        LANGUAGES[lang].title(): math.exp(prob) for lang, prob in lang_probs.items()
    }
    return (LANGUAGES[detect_language].title(), max_prob, all_probs)


def main(
    input_path: list,
    output_path: str = None,
    model_id: str = "large-v3",
    max_analysis_length: int = 120,
):
    """Main function to detect the language of the given audio file using the OpenAI Whisper model.

    Parameters:
    ------------
    input_path: list
        The path to the audio file to detect the language of or paths.
    output_path: str
        The path to save the results to. Default is None
    model_id: str
        The model id to use for language detection. Default is 'large-v3'.
    max_analysis_length: int
        The maximum number of frames to analyze. Default is 120 seconds of audio (16kHz * 120).
    """
    if output_path is None:
        output_path = os.path.join(
            os.getcwd(),
            f"whisper_language_detection_results_{now.strftime('%Y-%m-%d')}.txt",
        )
    else:
        p, ext = os.path.splitext(output_path)
        output_path = os.path.abspath(p + f"_{now.strftime('%Y-%m-%d')}" + ext)

    logging.info(
        "\n"
        + "*" * 10
        + "\n"
        + f"Running langage detection using OpenAI Whisper (model: {model_id})\n"
        + f"Maximum analysis length: {max_analysis_length} seconds\n"
        + f"Saving ouput to {output_path}\n"
        + "*" * 10
    )

    # load whisper model
    whisper_model = whisper.load_model(model_id)

    for audio_path in input_path:
        if not os.path.exists(audio_path):
            logging.error(f"File {audio_path} does not exist.")
            continue
        logging.info(f"Detecting language of {os.path.basename(audio_path)}...")
        detected_lang, prob, lang_probs = detect_language(
            audio_path, whisper_model, max_analysis_length=max_analysis_length * 16000
        )
        logging.info(f"Detected language: {detected_lang} with probability {prob}\n")
        logging.info(f"Language probabilities: {lang_probs}\n" + "---" * 10)
        # save results
        with open(output_path, "a") as f:
            f.write(f"{audio_path}: {detected_lang}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect the language of a given recording using the OpenAI Whisper."
    )
    parser.add_argument(
        "input_path",
        nargs="+",
        help="The path to the audio file to detect the language of. Either a single file, multiple files or a directory of files.",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="large-v3",
        help="The model id to use for language detection (OpenAI models). Default is 'large-v3'.",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=None,
        help="The path to save the results to. Default is whisper_language_detection_results\{date\}.txt",
    )
    parser.add_argument(
        "--max_analysis_length",
        type=int,
        default=120,
        help="The maximum length of audio to analyse. Default is 120 seconds of audio.",
    )
    args = parser.parse_args()

    # gather input paths
    input_paths = []
    for p in args.input_path:
        if os.path.isdir(p):
            input_paths.extend(
                [
                    os.path.abspath(os.path.join(p, f))
                    for f in os.listdir(p)
                    if os.path.splitext(f)[1] in EXTENSIONS
                ]
            )
        else:
            if os.path.splitext(p)[1] in EXTENSIONS:
                input_paths.append(os.path.abspath(p))
            else:
                logging.warning(
                    f"File {p} is not a supported audio file format. Supported formats are: {EXTENSIONS}"
                )

    main(
        input_path=input_paths,
        output_path=args.output_path,
        model_id=args.model_id,
        max_analysis_length=args.max_analysis_length,
    )
