"""This is a python script to help with Praat TextGrid management.

It contains functions to go back from table to TextGrid, combine TextGrids, and 
both functions at once.

Author: Alessandro De Luca
Date: 10-09-2024
"""

import argparse
import os
import pandas as pd
import parselmouth
from parselmouth.praat import call


class TextGridHanlder:
    """A class to handle TextGrid objects.

    Parameters:
    -----------
    filename: str
        The filename of the TextGrid file to load.
    t0_col: str, optional
        The name of the column containing the start times of the intervals.
        Default is 'tmin'. Only needed if filename is a table and not a .TextGrid file.
    t1_col: str, optional
        The name of the column containing the end times of the intervals.
        Default is 'tmax'. Only needed if filename is a table and not a .TextGrid file.
    tier_col: str, optional
        The name of the column containing the tier names.
        Default is 'tier_col'. Only needed if filename is a table and not a .TextGrid file.
    text_col: str, optional
        The name of the column containing the text.
        Default is 'text'. Only needed if filename is a table and not a .TextGrid file.

    Attributes:
    -----------
    textgrid: parselmouth.TextGrid
        The TextGrid object.

    Methods:
    --------
    _table_handler(filename: str) -> pd.DataFrame
        Handles the table file and returns a pandas.DataFrame.
    table_to_textgrid(table: pd.DataFrame, t0_col: str = 'tmin', t1_col: str = 'tmax',
                       tier_col: str = 'tier_col', text_col: str = 'text') -> parselmouth.TextGrid
        Converts a table to a TextGrid object.

    """

    def __init__(
        self,
        filename: str,
        t0_col: str = "tmin",
        t1_col: str = "tmax",
        tier_col: str = "tier_col",
        text_col: str = "text",
    ):
        if filename.endswith(".TextGrid"):
            self.textgrid = parselmouth.TextGrid(filename)
        else:
            self.textgrid = self.table_to_textgrid(
                table=self._table_handler(filename),
                t0_col=t0_col,
                t1_col=t1_col,
                tier_col=tier_col,
                text_col=text_col,
            )

    def _table_handler(self, filename: str):
        # find the separator
        with open(filename, "r") as f:
            line = f.readline()
            if len(line.split(",")) > 1:
                sep = ","
            elif len(line.split("\t")) > 1:
                sep = "\t"
            elif len(line.split(" ")) > 1:
                sep = " "
            elif len(line.split(";")) > 1:
                sep = ";"
            else:
                raise ValueError(
                    "Couldn't infer the separator from the file. Please provide a table file."
                )

        # read the table
        return pd.read_csv(filename, sep=sep)

    def table_to_textgrid(
        self,
        table: pd.DataFrame,
        t0_col: str = "tmin",
        t1_col: str = "tmax",
        tier_col: str = "tier_col",
        text_col: str = "text",
    ):
        """Converts a table to a TextGrid object.


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
        start = table[t0_col].min()
        end = table[t1_col].max()
        tiers = {k: 0 for k in set(table[tier_col])}

        # Create a new TextGrid
        tg = parselmouth.TextGrid(
            start_time=start, end_time=end, tier_names=list(tiers.keys())
        )

        # loop through the table and add the intervals
        for _, row in table.iterrows():
            ntier = (
                list(tiers.keys()).index(row[tier_col].value()) + 1
            )  # get the tier number
            nsegment = tiers[row[tier_col]] = (
                tiers[row[tier_col]] + 1
            )  # increment the counter for intervals
            t0 = row[t0_col]
            t1 = row[t1_col]
            text = row[text_col]

            # insert boundaries
            call(tg, "Insert boundary", ntier, t0)
            call(tg, "Insert boundary", ntier, t1)

            # insert text
            call(tg, "Set interval text", ntier, nsegment, text)

        return tg

    def add_tier(self, tier_name: str):
        """Adds a tier to the TextGrid.

        Parameters:
        -----------
        tier_name : str
            The name of the tier to add.
        """
        pass
