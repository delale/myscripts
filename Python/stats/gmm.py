"""Module to run Gaussian Mixture Model analyses.
"""
from copy import deepcopy
import pickle
import os
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.utils.extmath import softmax


def train_gmm_models(
    X: np.ndarray, speaker_names: np.ndarray, output_dir: str = None,
    n_components: int = 1024, max_iter: int = 200, n_init: int = 3,
    covariance_type: str = 'diag', reg_covar: float = 1e-6, random_state: int = 42
) -> dict:
    """Trains a GMM model for each speaker.

    Parameters:
    -----------
    X: np.ndarray
        Features of the speakers (n_files, n_frames, n_features).
    speaker_names: np.ndarray
        Speaker names with shape (n_files,)
    output_dir: str
        (Optional) Output directory to save the GMM models (saved with .gmm extension).
    n_components: int
        Number of components (mixtures) of the GMM.
    max_iter: int
        Maximum number of iterations for the EM algorithm.
    n_init: int
        Number of initializations for the EM algorithm.
    covariance_type: str
        Covariance type of the GMM. Default is 'diag'. See sklearn documentation for more options.
    reg_covar: float
        Regularization for the covariance matrix.X
    random_state: int
        Random state for reproducibility.

    Returns:
    --------
    GMM speaker models.
    """
    if X.shape[0] != speaker_names.shape[0]:
        raise ValueError(
            'X and speaker_names must have the same number of files.')
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    gmm_models = {}
    for speaker in np.unique(speaker_names):
        if len(X[speaker_names == speaker]) == 1:
            # Make sure to always use 2D arrays
            speaker_features = X[speaker_names == speaker][0]
        else:
            speaker_features = np.concatenate(
                X[speaker_names == speaker], axis=0)
        gmm = GaussianMixture(n_components=n_components, n_init=n_init, covariance_type=covariance_type,
                              max_iter=max_iter, reg_covar=reg_covar, random_state=random_state)
        gmm.fit(speaker_features)
        if output_dir:
            with open(f'{output_dir}/{speaker}.gmm', 'wb') as f:
                pickle.dump(gmm, f)
        gmm_models[speaker] = gmm

    return gmm_models


def map_adaptation(
        ubm: GaussianMixture, X: np.ndarray, output_path: str = None,
        max_iter: int = 1000, likelihood_threshold=1e-20, relevance_factor=16
):
    """Performs MAP adaptation of a GMM model.

    Parameters:
    -----------
    gmm: GaussianMixture
        GMM model to adapt.
    X: np.ndarray
        Features to adapt the GMM model.
    output_path: str
        (Optional) Output path to save the adapted GMM model (saved with .gmm extension).
    max_iter: int
        Maximum number of iterations for the EM algorithm.
    likelihood_threshold: float
        Likelihood threshold to stop the EM algorithm.
    relevance_factor: float
        Relevance factor for the MAP adaptation.

    Returns:
    --------
    Adapted GMM model.
    """
    gmm = deepcopy(ubm)
    # Strip any extension from the output path
    if output_path and '.' in output_path:
        output_path = output_path.split('.')[0]

    N = X.shape[0]
    D = X.shape[1]
    K = gmm.n_components

    mu_new = np.zeros((K, D))
    n_k = np.zeros((K, 1))

    # Initialize the values
    mu_k = gmm.means_

    # Initialize likelihoods
    old__likelihood = gmm.score(X)
    new_likelihood = 0

    iterations = 0
    # Perform MAP adaptation
    while (abs(old__likelihood - new_likelihood) > likelihood_threshold and iterations < max_iter):
        iterations += 1

        # E-step
        old__likelihood = new_likelihood
        z_n_k = gmm.predict_proba(X)
        n_k = np.sum(z_n_k, axis=0)

        # M-step
        for i in range(K):
            temp = np.zeros((1, D))
            for n in range(N):
                temp += z_n_k[n, i] * X[n, :]

            mu_new[i] = (1/n_k[i]) * temp

        # Adatapt the means
        adaptation_coefficient = n_k / (n_k + relevance_factor)
        for k in range(K):
            mu_k[k] = adaptation_coefficient[k] * mu_new[k] + \
                ((1 - adaptation_coefficient[k]) * mu_k[k])
        gmm.means_ = mu_k

        new_likelihood = gmm.score(X)
        print(f'Iteration {iterations}: {new_likelihood}')

    print('*' * 15)
    if abs(old__likelihood - new_likelihood) > likelihood_threshold:
        print('Warning: Maximum number of iterations reached.')
    else:
        print('Converged')

    if output_path:
        with open(f'{output_path}.gmm', 'wb') as f:
            pickle.dump(gmm, f)

    return gmm


def load_gmm_models(
    gmm_dir: str
):
    """Loads GMM models from a directory.

    Parameters:
    -----------
    gmm_dir: str
        Directory with the GMM models (saved with .gmm extension).

    Returns:
    --------
    GMM speaker models.
    """
    gmm_models = {}
    for file in os.listdir(gmm_dir):
        if file.endswith('.gmm'):
            with open(f'{gmm_dir}/{file}', 'rb') as f:
                gmm_models[file.replace('.gmm', '')] = pickle.load(f)

    return gmm_models


def predict_gmm_models(
    x: np.ndarray, speaker_models: dict,
):
    """Predicts the speaker of the input features.

    Parameters:
    -----------
    x: np.ndarray
        Input features to predict the speaker.
    speaker_models: dict
        Speaker models dictionary with key: speaker_name and value: GMM model.

    Returns:
    --------
    Predicted speaker.
    probs_dict: dict
        Dictionary with the probabilities of each speaker.
    """
    log_likelihoods = {
        speaker_name: gmm.score(x) for speaker_name, gmm in speaker_models.items()
    }

    # Calculate probabilities
    probs = softmax(np.array(list(log_likelihoods.values())
                             ).reshape(1, -1)).reshape(-1)
    probs_dict = {speaker_name: prob for speaker_name,
                  prob in zip(log_likelihoods.keys(), probs)}

    return max(log_likelihoods, key=log_likelihoods.get), probs_dict


def same_different_task(
    x1: np.ndarray, x2: np.ndarray, speaker_models: dict
):
    """Same-different task between two input features.

    Parameters:
    -----------
    y1: np.ndarray
        Input features to compare of first sample.
    y2: np.ndarray
        Input features to compare of second sample.
    speaker_models: dict
        Speaker models dictionary with key: speaker_name and value: GMM model.

    Returns:
    --------
    1 if same speaker, 0 if different speaker.
    probs: tuple
        Tuple with the probabilities of same and different speaker.
    """
    s1, probs_dict1 = predict_gmm_models(x1, speaker_models)
    s2, probs_dict2 = predict_gmm_models(x2, speaker_models)

    # Compute joint probability of same speaker
    same_speaker_prob = probs_dict1[s1] * probs_dict2[s1]
    diff_speaker_prob = 1 - same_speaker_prob
    probs = (same_speaker_prob, diff_speaker_prob)

    return 1 if s1 == s2 else 0, probs
