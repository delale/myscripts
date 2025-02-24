"""A script to synthesise audio from images.
The spectrogram of the audio will resemble the input image.
"""

import argparse
import os
from PIL import Image
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
import multiprocessing as mp


def preprocess_img(
    img_path: str,
):
    # Load img
    return Image.open(img_path).convert("L")


def prep_wave(
    duration: float,
    sample_rate: float,
):
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    audio_wave = np.zeros_like(t)

    return t, audio_wave


def _process_pixel(
    image: Image.Image,
    x: int,
    y: int,
    t: np.ndarray,
    fmin: float,
    fmax: float,
):
    pixel_value = image.getpixel((x, y))
    frequency = fmin + fmax - fmin * (pixel_value / 255)  # map pixel to Hz
    return np.sin(2 * np.pi * frequency * t)


def image_to_audio(
    image: Image.Image,
    audio_wave: np.ndarray,
    t: np.ndarray,
    freq_range: tuple,
):
    width, height = image.size
    fmin, fmax = freq_range
    with mp.Pool() as pool:
        results = pool.starmap(
            _process_pixel,
            [(image, x, y, t, fmin, fmax) for x in range(width) for y in range(height)],
        )

    for result in results:
        audio_wave += results

    # normalise
    audio_wave /= np.max(np.abs(audio_wave))

    return audio_wave


def plot_and_play(
    audio_wave: np.ndarray,
    sample_rate: float,
    duration: float,
):
    # play audio
    sd.play(audio_wave, blocking=True, samplerate=sample_rate)

    # plot waveform and spectrogram
    time = np.linspace(0, duration, len(audio_wave), False)
    f, t, Sxx = spectrogram(
        audio_wave,
        fs=sample_rate,
        nperseg=1024,
    )  # spec

    fig, ax = plt.subplots(1, 2, figsize=(12, 12))

    ax[0].plot(time, audio_wave)
    ax[0].set_xlabel("")
    ax[0].set_ylabel("Amplitude")

    ax[1].pcolormesh(t, f, Sxx, shading="gouraud", cmap="gray")
    ax[1].set_xlabel("Time (s)")
    ax[1].set_ylabel("Frequency (Hz)")

    plt.subplots_adjust(hspace=0.5)
    plt.show()


def main(
    img_path: str,
    save_to: str = None,
    duration: float = 5.0,
    sample_rate: float = 44100.0,
    freq_range: tuple[float] = (20.0, 12000.0),
    view_and_play: bool = False,
):
    image = preprocess_img(img_path)

    t, audio_wave = prep_wave(duration, sample_rate)

    image_wave = image_to_audio(image, audio_wave, t, freq_range)

    if save_to is None:
        save_to = os.path.splitext(img_path) + ".wav"

    sd.write(save_to, image_wave, sample_rate)
    print(f"Audio saved to {save_to}")

    if view_and_play:
        plot_and_play()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A program to encode an image into an audio file."
    )
    parser.add_argument(
        "img_path",
        help="Path of the image to encode.",
        type=str,
    )
    parser.add_argument(
        "--save_to",
        help="(Optional) Path to save the WAV file to.",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--duration",
        help="Audio duration in seconds. Default = 5.0 s.",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--sample_rate",
        help="Audio sample_rate. Default = 44100.0.",
        type=float,
        default=44100.0,
    )
    parser.add_argument(
        "--frequency_range",
        help="Audio frequency range in Hz; expecting 2 float values. Default = 20.0 12000.0.",
        type=float,
        nargs=2,
        default=(20.0, 12000.0),
    )
    parser.add_argument(
        "--view_and_play",
        help="Optional flag to play the audio and view the spectrogram after encoding. Default = False",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    args = parser.parse_args()

    main(
        img_path=args.img_path,
        save_to=args.save_to,
        duration=args.duration,
        sample_rate=args.sample_rate,
        freq_range=args.frequency_range,
        view_and_play=args.view_and_play,
    )
