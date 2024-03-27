"""Speaker verification using pretrained ECAPA-TDNN model.
"""

from speechbrain.inference.speaker import SpeakerRecognition
import torchaudio


def ecapa_verify(comparison_file: str, suspected_file: str):
    """Speaker verification using pretrained ECAPA-TDNN model.

    Parameters:
    -----------
    comparison_file: str
        File path of the comparison speaker.
    suspected_file: str
        File path of the suspected speaker.

    Returns:
    --------
    1 if same speaker, 0 if different speaker.
    """
    # Load the model
    model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb", savedir=".pretrained")

    # Load the audio files
    comparison_signal, sr = torchaudio.load(comparison_file)
    # Check that sr = 16000
    if sr != 16000:
        # resample
        comparison_signal = torchaudio.functional.resample(
            comparison_signal, orig_freq=sr, new_freq=16000)
    suspected_signal, sr = torchaudio.load(suspected_file)
    # Check that sr = 16000
    if sr != 16000:
        # resample
        suspected_signal = torchaudio.functional.resample(
            suspected_signal, orig_freq=sr, new_freq=16000)

    # Verify
    _, prediction = model.verify_batch(comparison_signal, suspected_signal)

    return prediction
