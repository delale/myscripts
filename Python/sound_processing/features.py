# --------------------------------------- #
# Alessandro De Luca 29/04/2022           #
# --------------------------------------- #

# IMPORTS #
import scipy.signal
import numpy
import librosa
import numpy as np
import pandas as pd
import scipy


def features(
        data_df: pd.DataFrame, n_mels=20, n_mfcc=13, n_fft=2048, window_length=25,
        overlap=10, lifter=22, premph_coef=0.95, fmin=150, fmax=8000,
        n_subsamples=0, seed=42
) -> 'tuple[np.array, np.array, np.array]':
    """Calculates MFCCs, Deltas, Delta-Deltas.

    Args:
        data_df: Dataframe containing information about audio files.
        n_mels: Number of mel-filters (default=20).
        n_mfcc: Number of MFCCs to extract (default=13).
        n_fft: FFT window length (default=2048).
        window_length: Window length in ms (default=25).
        overlap: Amount of overlap between successive windows in ms (default=10).
        premph_coef: Premphasis coefficient [0<=x<=1] (default=0.95).
        fmin: Minimum frequency of bandwidth in Hz (default=150).
        fmax: Maximum frequency of bandwidth in Hz (default=8000).
        n_subsamples: Number of sample per audio file if wanting to subsample
            (default=0).
        seed: Seed for random number generator (default=42).

    Returns:
        MFCCs, first order derivative, second order derivative.
    """

    # random number generator
    rng = np.random.RandomState(seed=seed)  # pylint: disable=no-member

    # init arrays for coeffircients, 1st and 2nd derivatives
    mfccs = []
    delta = []
    delta_second = []

    # init empty df column for reference to array indexes
    data_df["IndexRef"] = pd.Series(dtype='object')
    start_idx = 0

    # start looping through files
    for i, f in enumerate(data_df["Path"]):  # pylint: disable=invalid-name
        # load files and sample rates
        sig, sr = librosa.load(f, sr=None)  # pylint: disable=invalid-name

        if n_subsamples:
            sig = rng.choice(sig, size=n_subsamples, replace=True)

        # pre-emphasis
        sig = librosa.effects.preemphasis(y=sig, coef=premph_coef)

        # extract mfccs
        tmp_coefs = librosa.feature.mfcc(
            y=sig,
            sr=sr,
            n_mfcc=n_mfcc,
            lifter=lifter,
            window="hamming",
            win_length=int(window_length/1000 * sr),
            hop_length=int((window_length/1000-overlap/1000) * sr),
            n_fft=n_fft,
            n_mels=n_mels,
            fmin=fmin,
            fmax=fmax
        )
        mfccs.append(tmp_coefs.T)

        # calculate derivatives
        delta.append(librosa.feature.delta(tmp_coefs, order=1).T)
        delta_second.append(librosa.feature.delta(tmp_coefs, order=2).T)

        # add refernce index tuple
        last_idx = start_idx + tmp_coefs.shape[1]
        data_df.iat[i, -1] = (start_idx, last_idx)
        start_idx = last_idx

    print("COMPLETE: feature extraction")
    return (
        np.concatenate(mfccs, axis=0),
        np.concatenate(delta, axis=0),
        np.concatenate(delta_second, axis=0)
    )


def _frame_signal(audio, FFT_size=2048, window_length=25, overlap=10, sr=44100):
    hop = (window_length - overlap) / 1000
    frame_len = np.round(sr * hop).astype(int)
    frame_num = int((len(audio) - FFT_size) / frame_len) + 1

    # padding
    audio = np.pad(audio, FFT_size//2, mode='reflect')

    frames = np.zeros(shape=(frame_num, FFT_size))

    # framing
    for ii in range(frame_num):
        frames[ii] = audio[ii*frame_len:ii*frame_len + FFT_size]

    return frames


def _frft(f, a):
    """
    Calculate the fast fractional fourier transform.
    Parameters
    ----------
    f : numpy array
        The signal to be transformed.
    a : float
        fractional power
    Returns
    -------
    data : numpy array
        The transformed signal.
    References
    ---------
     .. [1] This algorithm implements `frft.m` from
        https://nalag.cs.kuleuven.be/research/software/FRFT/
    """
    # from https://github.com/nanaln/python_frft/blob/master/frft/frft.py#L2

    ret = numpy.zeros_like(f, dtype=numpy.complex)
    f = f.copy().astype(numpy.complex)
    N = len(f)
    shft = numpy.fmod(numpy.arange(N) + numpy.fix(N / 2), N).astype(int)
    sN = numpy.sqrt(N)
    a = numpy.remainder(a, 4.0)

    # # Special cases
    # if a == 0.0:
    #     return f
    # if a == 2.0:
    #     return numpy.flipud(f)
    # if a == 1.0:
    #     ret[shft] = numpy.fft.fft(f[shft]) / sN
    #     return ret
    # if a == 3.0:
    #     ret[shft] = numpy.fft.ifft(f[shft]) * sN
    #     return ret

    # reduce to interval 0.5 < a < 1.5
    if a > 2.0:
        a = a - 2.0
        f = numpy.flipud(f)
    if a > 1.5:
        a = a - 1
        f[shft] = numpy.fft.fft(f[shft]) / sN
    if a < 0.5:
        a = a + 1
        f[shft] = numpy.fft.ifft(f[shft]) * sN

    # the general case for 0.5 < a < 1.5
    alpha = a * numpy.pi / 2
    tana2 = numpy.tan(alpha / 2)
    sina = numpy.sin(alpha)
    f = numpy.hstack(
        (numpy.zeros(N - 1), _sincinterp(f), numpy.zeros(N - 1))).T

    # chirp premultiplication
    chrp = numpy.exp(-1j * numpy.pi / N * tana2 / 4 *
                     numpy.arange(-2 * N + 2, 2 * N - 1).T ** 2)
    f = chrp * f

    # chirp convolution
    c = numpy.pi / N / sina / 4
    ret = scipy.signal.fftconvolve(
        numpy.exp(1j * c * numpy.arange(-(4 * N - 4), 4 * N - 3).T ** 2),
        f
    )
    ret = ret[4 * N - 4:8 * N - 7] * numpy.sqrt(c / numpy.pi)

    # chirp post multiplication
    ret = chrp * ret

    # normalizing constant
    ret = numpy.exp(-1j * (1 - a) * numpy.pi / 4) * ret[N - 1:-N + 1:2]

    return ret


def _sincinterp(x):
    # from https://github.com/nanaln/python_frft/blob/master/frft/frft.py#L2
    N = len(x)
    y = numpy.zeros(2 * N - 1, dtype=x.dtype)
    y[:2 * N:2] = x
    xint = scipy.signal.fftconvolve(
        y[:2 * N],
        numpy.sinc(numpy.arange(-(2 * N - 3), (2 * N - 2)).T / 2),
    )
    return xint[2 * N - 3: -2 * N + 3]


def frCC(
    data_df: pd.DataFrame, n_mels=20, n_mfccs=13, n_fft=2048,
    window_length=25, overlap=10, premph_coef=0.95, alpha=0.70, fmin=150, fmax=8000,
    n_subsamples=0, seed=42
) -> 'tuple[np.array, np.array, np.array]':
    """Extraction of fractional Mel cepstral coefficients.

        Args:
            data_df: Dataframe containing information about audio files.
            n_mels: Number of mel-filters (default=20).
            n_mfcc: Number of MFCCs to extract (default=13).
            n_fft: FFT window length (default=2048).
            window_length: Window length in ms (default=25).
            overlap: Amount of overlap between successive windows in ms (default=10).
            premph_coef: Premphasis coefficient [0<=x<=1] (default=0.95).
            alpha: order of fractional Fourier transform (*pi) (default=0.70).
            fmin: Minimum frequency of bandwidth in Hz (default=150).
            fmax: Maximum frequency of bandwidth in Hz (default=8000).
            n_subsamples: Number of sample per audio file if wanting to subsample
                (default=0).
            seed: Seed for random number generator (default=42).

        Returns:
            Fractional Mel cepstral coefficients.
        """
    # radom number generator
    rng = np.random.RandomState(seed=seed)

    # init arrays for coeffircients, 1st and 2nd derivatives
    frccs = []
    delta = []
    delta_second = []

    # init empty df column for reference to array indexes
    data_df["IndexRef"] = pd.Series(dtype='object')
    start_idx = 0

    # window function
    window = scipy.signal.get_window("hamming", n_fft, fftbins=True)

    # start looping through files
    for i, f in enumerate(data_df["Path"]):
        # load files and sample rates
        sig, sr = librosa.load(f, sr=None)

        if n_subsamples:
            sig = rng.choice(sig, size=n_subsamples, replace=True)

        # preemphasis signal
        sig = librosa.effects.preemphasis(sig, coef=premph_coef)

        # signal framing
        sig_framed = _frame_signal(
            audio=sig, sr=sr, FFT_size=n_fft,
            window_length=window_length, overlap=overlap
        )

        # windowing
        sig_win = sig_framed * window
        sig_win = sig_win.T

        # fractional fourier transform
        sig_frfft = np.empty(
            (int(1 + 2048 // 2), sig_win.shape[1]), dtype=np.complex64, order='F')

        for n in range(sig_frfft.shape[1]):
            sig_frfft[:, n] = _frft(sig_win[:, n], a=alpha)[
                :sig_frfft.shape[0]]

        sig_frfft = np.transpose(sig_frfft)

        # signal power
        sig_pwr = np.square(np.abs(sig_frfft))

        # mel filters
        mel_filters = librosa.filters.mel(
            sr=sr, n_fft=n_fft, n_mels=n_mels, fmin=fmin, fmax=fmax
        )
        sig_filtered = np.dot(mel_filters, sig_pwr.T)
        sig_log = 10.0 * np.log10(sig_filtered)
        sig_log = sig_log.T

        # DCT
        # transposed for consistency with librosa mfcc output shape
        tmp_coefs = scipy.fftpack.dct(sig_log, type=3, n=n_mfccs).T

        frccs.append(tmp_coefs.T)

        # calculate derivatives
        delta.append(librosa.feature.delta(tmp_coefs, order=1).T)
        delta_second.append(librosa.feature.delta(tmp_coefs, order=2).T)

        # add refernce index tuple
        last_idx = start_idx + tmp_coefs.shape[1]
        data_df.iat[i, -1] = (start_idx, last_idx)
        start_idx = last_idx

    print("COMPLETE: feature extraction")
    return (
        np.concatenate(frccs, axis=0),
        np.concatenate(delta, axis=0),
        np.concatenate(delta_second, axis=0)
    )


def get_ref(reference: pd.Series) -> np.array:
    """Get reference to new arrays.

    Takes the 'IndexRef' column of the dataframe and creates a concatenated
    reference for all indexes contained in the reference series. It takes the
    tuple containg the start and ending of the reference and creates the range
    from start to end.

    Args:
        reference: Reference indeces series, each in the form (start, end).

    Returns:
        The concatenated reference indeces.
    """

    if not type(reference) == tuple:
        concat_reference = [
            np.arange(x[0], x[1]) for x in reference
        ]

        return np.concatenate(concat_reference)

    else:
        return np.arange(reference[0], reference[1])


def z_normalize(
    data_df: pd.DataFrame, mfccs: np.array,
    delta: np.array, delta_second: np.array
) -> None:
    """Within speaker Z-normalization.

    Args:
        data_df: Dataframe containing information about audio files.
        mfccs: MFCCs array.
        delta: First derivative of the MFCCs array.
        delta_second: Second derivative of the MFCCs array.
    """

    # loop over all individuals and normalize
    for ind in data_df["ParticipantID"].unique():
        # concatenate speakers indexes for arrays
        reference = get_ref(
            reference=data_df.loc[data_df["ParticipantID"] == ind, "IndexRef"]
        )

        # normalize coefficients
        if mfccs is not None:
            mfccs[reference] = (mfccs[reference] - np.mean(mfccs[reference], axis=0)) / \
                np.std(mfccs[reference], axis=0)
        if delta is not None:
            delta[reference] = (delta[reference] - np.mean(delta[reference], axis=0)) / \
                np.std(delta[reference], axis=0)
        if delta_second is not None:
            delta_second[reference] = (delta_second[reference] -
                                       np.mean(delta_second[reference], axis=0)) / \
                np.std(delta_second[reference], axis=0)

    print("COMPLETED: normalization!")


if __name__ == "__main__":
    df = create_df(data_folder="testData/")

    # TEST features()
    m, d, d2 = features(data_df=df)

    print(f'MFCCS: {m.shape}\nD: {d.shape}\nD2: {d2.shape}')
    print("MFCCS:")
    print(m[:10])

    print(f'DF columns: {df.columns}')

    # TEST z_normalize()
    print('START Z-normalization')
    z_normalize(
        data_df=df, mfccs=m, delta=d, delta_second=d2
    )

    print('COMPLETED')
