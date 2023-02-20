"""
Module to manipulate audio recordings of meerkat close-calls.
Manipulation options:
- noise injection
- signal shifting
- pitch shifting using librosa (tries to reconstruct formant spacing on new f0)
- pitch shifting using numpy (does not reconstruct formant spacing on new f0)
- harmonic distortion
- f0 shifting
- formant shifting
- f0 or formant masking

Author: Alessandro De Luca
Month/Year: 02/2022
"""

import pandas as pd
import numpy as np
import librosa
import librosa.display
import soundfile
import glob
import matplotlib
import matplotlib.image
import matplotlib.pyplot as plt


def add_noise(noise_directory, signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Adds random amount of noise to signal creating 'how_many' augmented signals up to N.
    Saves signals and returns modified metadat dataset containing the new files' paths.

    Args:
        noise_directory: [str] directory of noise samples
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # load noise
    filenames = glob.glob(noise_directory+"*.wav")

    noise = []

    for i in filenames:
        signal, _ = librosa.load(i, sr=None)
        noise.append(signal)

    # copy metadata dataset
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        selection = [np.random.randint(
            0, len(noise) - 1) for j in range(how_many)]

        # noise augmentation
        for k in selection:

            # resize noise to siganl dims
            tmp_noise = np.resize(noise[k], sig.shape)

            # augment signal
            augmented = sig + tmp_noise

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr
            )

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        # select random noise sample
        tmp_noise = noise[np.random.randint(0, len(noise)-1)]

        # resize noise to siganl dims
        tmp_noise = np.resize(tmp_noise, sig.shape)

        # augment signal
        augmented = sig + tmp_noise

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def shift(signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Shifts signal creating `how_many` augmented signals.
    Then also saves this signals in the augmented/ directory.

    Args:
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # copy of metadata
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original calls

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        # shift augmentation
        for k in range(how_many):

            # get random shift:
            s = int(np.random.choice(
                [-1, 1]) * np.random.uniform(0.1, 0.3) * len(sig))

            augmented = np.roll(sig, s)

            # padding
            if s > 0:
                augmented[:s] = 0
            else:
                augmented[s:] = 0

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        # get random shift:
        s = int(np.random.choice(
            [-1, 1]) * np.random.uniform(0.1, 0.3) * len(sig))

        augmented = np.roll(sig, s)

        # padding
        if s > 0:
            augmented[:s] = 0
        else:
            augmented[s:] = 0

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def pitch_shift_librosa(min_shift_Hz, max_shift_Hz, signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Pitch shifting using librosa.effects.pitch_shift creating `how_many` augmented signals.
    librosa.effects.pitch_shift tries to shift f0 and then recompute the formant 
    spacing according to the new f0.
    Then also saves this signals in the augmented/ directory.

    Formula: f1 = f0*2^(s/12) (s=num. steps)
            s = 12 log_2(1 + F_shift/f0)
            f0 = i/N * sr (i=pos.max.magn, N=num.samples)

    Args:
        min_shift_Hz: [float] minimum amount to shift in Hz
        max_shift_Hz: [float] maximum amount to shift in Hz 
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """
    # copy metadata
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random_state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        sig_fft = np.fft.rfft(sig)
        f0 = np.where(sig_fft == np.max(sig_fft))
        f0 = f0[0] / len(sig) * sr
        # avoid 0 division later
        if not(f0 > 0.0):
            f0 = f0 + 0.3

        for k in range(how_many):

            up_down = np.random.choice([-1, 1])  # shift up or down
            shift_Hz = np.random.uniform(min_shift_Hz, max_shift_Hz)
            s = up_down * 12 * np.log2(1 + shift_Hz/f0)

            augmented = librosa.effects.pitch_shift(
                y=sig, sr=sr, n_steps=s)

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        sig_fft = np.fft.rfft(sig)  # signal fft
        f0 = np.where(sig_fft == np.max(sig_fft))
        f0 = f0[0] / len(sig) * sr
        # avoid 0 division later
        if not(f0 > 0.0):
            f0 = f0 + 0.3

        up_down = np.random.choice([-1, 1])  # shift up or down
        shift_Hz = np.random.uniform(min_shift_Hz, max_shift_Hz)
        s = up_down * 12 * np.log2(1 + shift_Hz/f0)

        augmented = librosa.effects.pitch_shift(
            y=sig, sr=sr, n_steps=s)

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def pitch_shift_numpy(min_shift_Hz, max_shift_Hz, signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Pitch shifting using numpy creating `how_many` augmented signals.
    Does not recompute formant spacing based on new f0.
    Then also saves this signals in the augmented/ directory.
    Formula: F_shift:sr=shift:N (N=num. samples)
            shift = round(F_shift * N / sr)

    Args:
        min_shift_Hz: [float] minimum amount to shift in Hz
        max_shift_Hz: [float] maximum amount to shift in Hz 
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # copy metadata
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        sig_fft = np.fft.rfft(sig)  # fft of signal

        for k in range(how_many):

            shift_Hz = np.random.choice(
                [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

            s = int(np.round(shift_Hz * len(sig) / sr))
            augmented = np.roll(sig_fft, s)
            augmented = np.fft.irfft(augmented)

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        sig_fft = np.fft.rfft(sig)  # fft of signal

        shift_Hz = np.random.choice(
            [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

        s = int(np.round(shift_Hz * len(sig) / sr))
        augmented = np.roll(sig_fft, s)
        augmented = np.fft.irfft(augmented)

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def harmonic_dist(signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Harmonic distortion creating `how_many` augmented signals.
    Distorts signal by recomputing amplitude and multiplying by amount of distortion.
    Then also saves this signals in the augmented/ directory.
    Formula: sig_out = amount * sin(2*pi*sig_in)

    Args:
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # copy metadata
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        for k in range(how_many):

            # how much harmonic distortion to keep
            amount = np.random.uniform(0.6, 1.0)
            augmented = amount * np.sin(2 * np.pi * sig)

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        # how much harmonic distortion to keep
        amount = np.random.uniform(0.6, 1.0)
        augmented = amount * np.sin(2 * np.pi * sig)

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def shift_f0(min_shift_Hz, max_shift_Hz, signals, sample_rates, metadata, save_directory, N, seed=42):
    """
    Shifting fundamental frequency using numpy creating `how_many` augmented signals.
    Then also saves this signals in the augmented/ directory.
    Formula: F_shift:sr=shift:N (N=num. samples)
            shift = round(F_shift * N / sr)

    Args:
        min_shift_Hz: [float] minimum amount to shift in Hz
        max_shift_Hz: [float] maximum amount to shift in Hz
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # copy metadata
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        sig_freq = np.fft.rfft(sig)  # sig fft
        sig_freq_abs = np.abs(sig_freq)  # absolute sig fft

        f0 = np.where(sig_freq_abs == np.max(
            sig_freq_abs))[0]  # fundamental

        start = (f0 - 30)[0]
        end = (f0 + 31)[0]

        if start < 0:
            start = 0
        if end > (len(sig_freq) - 1):
            end = len(sig_freq) - 1

        # noise for substitution (from the same signal)
        where_noise = np.where(
            (sig_freq_abs < np.max(sig_freq_abs) * 0.05))

        noise = np.random.choice(sig_freq[where_noise], size=len(
            sig_freq[start:end]))  # random noise

        for k in range(how_many):

            shift_Hz = np.random.choice(
                [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

            s = int(np.round(shift_Hz * len(sig) / sr))

            if (start + s) < 0:
                s *= -1
            elif (end + s) > (len(sig_freq) - 1):
                s *= -1

            augmented = sig_freq.copy()

            start_s = start + s
            end_s = end + s

            augmented[start:end] = noise
            augmented[start_s:end_s] = sig_freq[start:end]
            augmented = np.fft.irfft(augmented)

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        sig_freq = np.fft.rfft(sig)  # sig fft
        sig_freq_abs = np.abs(sig_freq)  # absolute sig fft

        f0 = np.where(sig_freq_abs == np.max(
            sig_freq_abs))[0]  # fundamental

        start = (f0 - 30)[0]
        end = (f0 + 31)[0]

        if start < 0:
            start = 0
        if end > (len(sig_freq) - 1):
            end = len(sig_freq) - 1

        # noise for substitution (from the same signal)
        where_noise = np.where(
            (sig_freq_abs < np.max(sig_freq_abs) * 0.05))

        noise = np.random.choice(sig_freq[where_noise], size=len(
            sig_freq[start:end]))  # random noise

        shift_Hz = np.random.choice(
            [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

        s = int(np.round(shift_Hz * len(sig) / sr))

        if (start + s) < 0:
            s *= -1
        elif (end + s) > (len(sig_freq) - 1):
            s *= -1

        augmented = sig_freq.copy()

        start_s = start + s
        end_s = end + s

        augmented[start:end] = noise
        augmented[start_s:end_s] = sig_freq[start:end]
        augmented = np.fft.irfft(augmented)

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def shift_formants(min_shift_Hz, max_shift_Hz, signals, sample_rates, metadata, save_directory, N, seed=42, threshold=0.15):
    """
    Shifting higher harmonics using numpy creating `how_many` augmented signals.
    Then also saves this signals in the augmented/ directory.
    Formula: F_shift:sr=shift:N (N=num. samples)
            shift = round(F_shift * N / sr)

    Args:
        min_shift_Hz: [float] minimum amount to shift in Hz
        max_shift_Hz: [float] maximum amount to shift in Hz
        signals: [list] list of signals from librosa.load
        sample_rates: [list] list of sample rate of each signal
        metadata: [pd.DataFrame] metadata dataframe
        save_directory: [str] directory where to save the augmented files
        N: [int] how many signals
        seed [int]: default=42; random seed for reproducibility
        threshold [float]: default=0.15; lowest amount in relation to f0 to count as harmonic and not noise

    Returns:
        df: [pd.DataFrane] updated metadata dataframe with augmented file information
    """

    # ValueError
    if threshold > 1.0:
        raise ValueError("quantile should not be >1.0")

    # copy metadta
    df = metadata.copy(deep=True)

    np.random.seed(seed)  # random state

    n_calls = metadata.shape[0]  # how many original

    # how many augmented signals per original call
    how_many = (N-n_calls)//n_calls

    j = 0  # call counter

    for i, sig in enumerate(signals):

        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sr = sample_rates[i]  # sampling rate of the signal
        n = 1  # sequential numbering of augmented signals

        j += 1  # keep count also of original signals

        sig_freq = np.fft.rfft(sig)  # sig fft
        sig_freq_abs = np.abs(sig_freq)  # absolute sig fft

        formants = np.where((sig_freq_abs < np.max(sig_freq_abs))
                            * (sig_freq_abs > threshold * np.max(sig_freq_abs)))
        f0 = np.where(sig_freq_abs == np.max(
            sig_freq_abs))[0]  # fundamental

        # noise for substitution (from the same signal)
        where_noise = np.where(
            (sig_freq_abs < np.max(sig_freq_abs) * 0.05))

        for k in range(how_many):

            shift_Hz = np.random.choice(
                [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

            s = int(np.round(shift_Hz * len(sig) / sr))

            augmented = sig_freq.copy()

            for i in formants[0]:
                # exclude close to f0
                if i > (f0-30)[0] and i < (f0+31)[0]:
                    pass
                else:
                    start = (i - 15)
                    end = (i + 16)
                    if start < 0:
                        start = 0
                    if end > (len(sig_freq) - 1):
                        end = len(sig_freq) - 1

                    if (start + s) < 0:
                        s *= -1
                    elif (end + s) > (len(sig_freq) - 1):
                        s *= -1

                    start_s = start + s
                    end_s = end + s

                    # noise padding
                    noise = np.random.choice(sig_freq[where_noise], size=len(
                        sig_freq[start:end]))  # random noise
                    augmented[start:end] = np.random.choice(
                        noise, size=end-start)
                    augmented[start_s:end_s] = sig_freq[start:end]

            # inverse fft
            augmented = np.fft.irfft(augmented)

            # metadata rewrite
            tmp_series["CallFile"] = call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            new_path = save_directory + "\\" + call_file + \
                "_aug_{:02}".format(n) + ".WAV"
            tmp_series["Path"] = new_path
            n += 1

            df = df.append(tmp_series)

            # save augmented file
            soundfile.write(
                file=new_path, data=augmented, samplerate=sr)

            j += 1

    d = {}  # dictionary for correct sequential numbering of augmented calls

    # augment random signals again to reach N
    while j < N:

        # random original call
        i = np.random.randint(0, metadata.shape[0] - 1)
        # extract original call file metadata
        call_file = metadata["CallFile"].iloc[i][:-4]
        # create a metadata series obj to manipulate
        tmp_series = metadata.copy(deep=True).iloc[i]
        sig = signals[i]  # signal
        sr = sample_rates[i]  # sampling rate of the signal

        # sequential numbering
        if not(call_file in d.keys()):
            n = how_many + 1
            d["call_file"] = [n]
        else:
            n = how_many + 1 + len(d["call_file"])
            d["call_file"].append(n)

        sig_freq = np.fft.rfft(sig)  # sig fft
        sig_freq_abs = np.abs(sig_freq)  # absolute sig fft

        formants = np.where((sig_freq_abs < np.max(sig_freq_abs))
                            * (sig_freq_abs > threshold * np.max(sig_freq_abs)))
        f0 = np.where(sig_freq_abs == np.max(
            sig_freq_abs))[0]  # fundamental

        # noise for substitution (from the same signal)
        where_noise = np.where(
            (sig_freq_abs < np.max(sig_freq_abs) * 0.05))

        shift_Hz = np.random.choice(
            [-1, 1]) * np.random.uniform(min_shift_Hz, max_shift_Hz)

        s = int(np.round(shift_Hz * len(sig) / sr))

        augmented = sig_freq.copy()

        for i in formants[0]:
            # exclude close to f0
            if i > (f0-30)[0] and i < (f0+31)[0]:
                pass
            else:
                start = (i - 15)
                end = (i + 16)
                if start < 0:
                    start = 0

                if end > (len(sig_freq) - 1):
                    end = len(sig_freq) - 1

                if (start + s) < 0:
                    s *= -1
                elif (end + s) > (len(sig_freq) - 1):
                    s *= -1

                start_s = start + s
                end_s = end + s

                # noise padding
                noise = np.random.choice(sig_freq[where_noise], size=len(
                    sig_freq[start:end]))  # random noise
                augmented[start:end] = np.random.choice(
                    noise, size=end-start)
                augmented[start_s:end_s] = sig_freq[start:end]

        # inverse fft
        augmented = np.fft.irfft(augmented)

        # metadata rewrite
        tmp_series["CallFile"] = call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        new_path = save_directory + "\\" + call_file + \
            "_aug_{:02}".format(n) + ".WAV"
        tmp_series["Path"] = new_path
        n += 1

        df = df.append(tmp_series)

        # save augmented file
        soundfile.write(
            file=new_path, data=augmented, samplerate=sr)

        j += 1

    return df


def mask(signals, sample_rates, pass_type):
    """
    Masks frequency ranges depending on the pass type argument.
    Works specifically on meerkat close-calls (no common sub-harmonics).
    Can work on other call types that do not present sub-harmonics or, with small 
    modifications, where the fundamental frequency is the most intense frequency. 

    Args:
        signals: [ndarray] list of loaded signals
        sample_rates: [ndarray] list of the sample rates of each signal
        pass_type: [str] what pass filter to use; options are f0(only fundamental), fN(formants)

    Returns:
        sigs: [ndarray] list of the masked signals
    """

    if not(pass_type in ["f0", "fN"]):
        raise ValueError("pass_type has to be either \"f0\" or \"fN\"")

    sigs = []  # signals

    # pass formants = mask f0
    if pass_type == "fN":
        for i, sig in enumerate(signals):

            sr = sample_rates[i]

            sig_freq = np.fft.rfft(sig)  # sig fft
            sig_freq_abs = np.abs(sig_freq)  # absolute of sig fft

            f0 = np.where(sig_freq_abs == np.max(sig_freq_abs))[
                0] * sr / len(sig)  # fundamental

            where = int(f0 * 1.25 * len(sig) / sr)  # where to mask to

            # mask
            low_filtered = sig_freq.copy()
            low_filtered[:where] = 0.0

            # reverse fft * 2 to return to waveform
            low_filtered = np.fft.irfft(low_filtered) * 2

            sigs.append(low_filtered)

    # pass fundamental = mask f1...fN
    else:
        for i, sig in enumerate(signals):

            sr = sample_rates[i]

            sig_freq = np.fft.rfft(sig)  # sig fft
            sig_freq_abs = np.abs(sig_freq)  # absolute of sig fft

            f0 = np.where(sig_freq_abs == np.max(sig_freq_abs))[
                0] * sr / len(sig)  # fundamental

            where = int(f0 * 1.25 * len(sig) / sr)  # where to mask from

            # mask
            high_filtered = sig_freq.copy()
            high_filtered[where:] = 0.0

            # reverse fft * 2 to return to waveform
            high_filtered = np.fft.irfft(high_filtered) * 2

            sigs.append(high_filtered)

    return np.array(sigs)
