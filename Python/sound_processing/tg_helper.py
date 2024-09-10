"""This is a python script to help with Praat TextGrid management.

It contains functions to go back from table to TextGrid, combine TextGrids, and 
both functions at once.

Author: Alessandro De Luca
Date: 10-09-2024
"""
import os
import pandas as pd
import parselmouth
from parselmouth.praat import call

def table_to_textgrid(table, t0_col: str = 'tmin', t1_col: str = 'tmax', 
                      tier_col: str = 'tier_col', text_col: str = 'text'):
    """Convert a table to a TextGrid object.

    Parameters:
    -----------
    table : pandas.DataFrame
        The table to convert to TextGrid.
    t0_col : str, optional
        The name of the column containing the start times of the intervals.
        Default is 'tmin'.
    t1_col : str, optional
        The name of the column containing the end times of the intervals.
        Default is 'tmax'.
    tier_col : str, optional
        The name of the column containing the tier names.
        Default is 'tier_col'.
    text_col : str, optional
        The name of the column containing the text.
        Default is 'text'.

    Returns:
    --------
    textgrid : parselmouth.TextGrid
        The TextGrid object.
    """
    # init vars
    start = 
    end = table[t1_col].max()

    # Create a new TextGrid
    textgrid = parselmouth.TextGrid()