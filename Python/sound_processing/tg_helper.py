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
        Default is 'tier'. Only needed if filename is a table and not a .TextGrid file.
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
    _insert_segment(tg, ntier, nsegment, t0, t1, text) -> parselmouth.TextGrid
        Inserts a segment in the TextGrid.
    table_to_textgrid(table: pd.DataFrame, t0_col: str = 'tmin', t1_col: str = 'tmax',
                       tier_col: str = 'tier', text_col: str = 'text') -> parselmouth.TextGrid
        Converts a table to a TextGrid object.
    add_tier(tier_name: str, tier_table: pd.DataFrame, t0_col: str = 'tmin', t1_col: str = 'tmax',
             text_col: str = 'text') -> None
        Adds a tier to the TextGrid.
    save(filename: str) -> None
        Saves the TextGrid object to a file.
    """

    def __init__(
        self,
        filename: str,
        t0_col: str = "tmin",
        t1_col: str = "tmax",
        tier_col: str = "tier",
        text_col: str = "text",
    ):
        if filename.endswith(".TextGrid"):
            self.textgrid = parselmouth.read(filename)
            self.table = call(self.textgrid, "Down to table", 6, 1, 1)
        else:
            self._table_handler(filename)
            self.textgrid = self.table_to_textgrid(
                table=self.table,
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
        self.table = pd.read_csv(filename, sep=sep)

    def _insert_segment(self, tg, ntier, nsegment, t0, t1, text):
        is_interval = t0 != t1
        text = "" if pd.isna(text) else text

        if is_interval:
            # interval tier
            call(tg, "Insert boundary", ntier, t0)
            call(tg, "Insert boundary", ntier, t1)
            # insert text
            call(tg, "Set interval text", ntier, nsegment, text)
        else:
            # point tier
            call(tg, "Insert point", ntier, t0)
            # insert text
            call(tg, "Set point text", ntier, nsegment, text)

        return tg

    def table_to_textgrid(
        self,
        table: pd.DataFrame,
        t0_col: str = "tmin",
        t1_col: str = "tmax",
        tier_col: str = "tier",
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
            Default is 'tier'.
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
        self.tiers = {k: 0 for k in set(table[tier_col])}

        # Create a new TextGrid
        tg = parselmouth.TextGrid(
            start_time=start, end_time=end, tier_names=list(self.tiers.keys())
        )

        # loop through the table and add the intervals
        for _, row in table.iterrows():
            ntier = (
                list(self.tiers.keys()).index(row[tier_col].value()) + 1
            )  # get the tier number
            nsegment = self.tiers[row[tier_col]] = (
                self.tiers[row[tier_col]] + 1
            )  # increment the counter for intervals
            t0 = row[t0_col]
            t1 = row[t1_col]
            text = row[text_col]

            # insert the segment
            tg = self._insert_segment(tg, ntier, nsegment, t0, t1, text)

        return tg

    def add_tier(
        self,
        tier_name: str,
        tier_table: pd.DataFrame,
        t0_col: str = "tmin",
        t1_col: str = "tmax",
        text_col: str = "text",
    ):
        """Adds a tier to the TextGrid. The tier will be added at the end of the TextGrid.

        Parameters:
        -----------
        tier_name: str
            The name of the tier to add.
        tier_table : pd.DataFrame
            The name of the tier to add.
        t0_col : str, optional
            The name of the column containing the start times of the intervals.
            Default is 'tmin'.
        t1_col : str, optional
            The name of the column containing the end times of the intervals.
            Default is 'tmax'.
        text_col : str, optional
            The name of the column containing the text.
            Default is 'text'.
        """
        # get the tier number
        ntier = len(self.tiers) + 1

        # add the tier to the TextGrid
        call(self.textgrid, "Insert interval tier", ntier, tier_name)

        # loop through the table and add the intervals
        for nsegment, row in tier_table.iterrows():
            t0 = row[t0_col]
            t1 = row[t1_col]
            text = row[text_col]

            # insert the segment
            self.textgrid = self._insert_segment(
                self.textgrid, ntier, nsegment, t0, t1, text
            )

    def save(self, filename: str):
        """Saves the TextGrid object to a file.

        Parameters:
        -----------
        filename: str
            The filename to save the TextGrid to.
        """
        self.textgrid.save(filename)


# functions ####################################################################
def combine_textgrids(
    textgrids: list,
    output_filename: str,
    t0_col: str = "tmin",
    t1_col: str = "tmax",
    tier_col: str = "tier",
    text_col: str = "text",
) -> None:
    """Combine multiple textgrids into a single one.

    Parameters:
    -----------
    textgrids : list
        A list of TextGrid filenames to combine.
    output_filename : str
        The filename of the output TextGrid.
    t0_col : str, optional
        The name of the column containing the start times of the intervals.
        Default is 'tmin'.
    t1_col : str, optional
        The name of the column containing the end times of the intervals.
        Default is 'tmax'.
    tier_col : str, optional
        The name of the column containing the tier names.
        Default is 'tier'.
    text_col : str, optional
        The name of the column containing the text.
        Default is 'text'.
    """
    # Load the textgrids
    ref_tg = TextGridHanlder(
        filename=textgrids.pop(0),
        t0_col=t0_col,
        t1_col=t1_col,
        tier_col=tier_col,
        text_col=text_col,
    )  # reference textgrid
    to_add_tg = [
        TextGridHanlder(
            filename=f,
            t0_col=t0_col,
            t1_col=t1_col,
            tier_col=tier_col,
            text_col=text_col,
        )
        for f in textgrids
    ]

    # Add the tiers from the other textgrids
    for tg in to_add_tg:
        for tier_name in tg.tiers.keys():
            tier_table = tg.table[
                tg.table[tier_col] == tier_name
            ]  # extract only tier rows
            ref_tg.add_tier(
                tier_name, tier_table, t0_col, t1_col, text_col
            )  # add tier to ref

    # Save the combined textgrid
    ref_tg.save(output_filename)


# convert from table
def convert_to_textgrid(
    filename: str,
    output_filename: str,
    t0_col: str = "tmin",
    t1_col: str = "tmax",
    tier_col: str = "tier",
    text_col: str = "text",
) -> None:
    """Convert a table to a TextGrid.

    Parameters:
    -----------
    filename: str
        The filename of the table to convert.
    output_filename: str
        The filename of the output TextGrid.
    t0_col: str, optional
        The name of the column containing the start times of the intervals.
        Default is 'tmin'.
    t1_col: str, optional
        The name of the column containing the end times of the intervals.
        Default is 'tmax'.
    tier_col: str, optional
        The name of the column containing the tier names.
        Default is 'tier'.
    text_col: str, optional
        The name of the column containing the text.
        Default is 'text'.
    """
    tgHelper = TextGridHanlder(filename, t0_col, t1_col, tier_col, text_col)
    tgHelper.save(output_filename)


# main #########################################################################
def main():
    # parse the arguments
    parser = argparse.ArgumentParser(
        description="A script to help with Praat TextGrid management.\nMain functions are to convert a table to a TextGrid and to combine multiple TextGrids into a single one."
    )
    parser.add_argument(
        "function",
        type=str,
        choices=["convert", "combine"],
        help="The function to run. 'convert' to convert a table to a TextGrid and 'combine' to combine multiple TextGrids.",
    )
    parsed_args = parser.parse_args()

    # user inputs
    filename = input("Enter the filename (full path) of the table or the TextGrid: ")
    i = 0
    while output_filename == "" or i == 0:
        if i > 0:
            print("Please provide a valid filename.")
        output_filename = input("Enter the output filename (full path): ")
        i += 1
        if i > 5:
            raise ValueError("Too many attempts. Exiting.")
    t0_col = (
        input("Enter the column name for the start times [default='tmin']: ") or "tmin"
    )
    t1_col = (
        input("Enter the column name for the end times [default='tmax']: ") or "tmax"
    )
    tier_col = (
        input("Enter the column name for the tier names [default='tier']: ") or "tier"
    )
    text_col = input("Enter the column name for the text [default='text']: ") or "text"

    if parsed_args.function == "convert":
        convert_to_textgrid(
            filename, output_filename, t0_col, t1_col, tier_col, text_col
        )
    else:  # combine
        textgrids = [filename]
        while True:
            tg = input(
                "Enter the filename (full path) of the TextGrid(s) to combine. Enter 'q' to finish: "
            )
            textgrids.append(tg)
            if tg == "q":
                break
        combine_textgrids(
            textgrids, output_filename, t0_col, t1_col, tier_col, text_col
        )

    print("Done.\nYour new TextGrid is saved as:", output_filename)


if __name__ == "__main__":
    main()
