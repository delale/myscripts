"""Module to calculate geometry of voice space.
"""

import numpy as np


def euclidean_distance(x: np.ndarray, y: np.ndarray) -> float:
    """Measure the Euclidean distance between two vectors.

    Parameters:
    -----------
    x: np.ndarray
        First vector.
    y: np.ndarray
        Second vector.

    Returns:
    --------
    Distance between the two vectors.
    """
    return np.linalg.norm(x - y)


def manhattan_distance(x: np.ndarray, y: np.ndarray) -> float:
    """Measure the Manhattan distance between two vectors.

    Parameters:
    -----------
    x: np.ndarray
        First vector.
    y: np.ndarray
        Second vector.

    Returns:
    --------
    Distance between the two vectors.
    """
    return np.sum(np.abs(x - y))


def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
    """Measure the cosine similarity between two vectors.

    Parameters:
    -----------
    x: np.ndarray
        First vector.
    y: np.ndarray
        Second vector.

    Returns:
    --------
    Cosine similarity between the two vectors.
    """
    return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))
