"""This is a python script to help with Praat TextGrid management.

It contains functions to go back from table to TextGrid, combine TextGrids, and 
both functions at once.

Author: Alessandro De Luca
Date: 10-09-2024
--------------------------------------------------------------------------------
Usage:
------
1. Run the script.
2. Choose the function to run: 'convert' or 'combine'.
3. Enter the filename of the table or the TextGrid.
4. Enter the output filename.
5. Enter the column names for the start times, end times, tier names, and text.
6. If combining TextGrids, enter the filenames of the TextGrids to combine.
7. The new TextGrid will be saved in the output filename.

Caveats:
--------
- The script assumes that the table has a header.
- The script assumes that the table has a separator.
- When combining TextGrids it is advisable to keep Praat's default column names ['tmin', 'tmax', 'tier', 'text'].
    In case you are using tables to combine TextGrids, the script will use the column names you provide; make sure they are consistent across tables.
- When combining TextGrids, the script will add a suffix to the tier name if it already exists in the reference TextGrid.

Example:
--------
converting a table to a TextGrid:
$ python tg_helper.py convert
> Enter the filename (full path) of the table or the TextGrid: /path/to/table.csv
> Enter the output filename (full path): /path/to/output.TextGrid
> Enter the column name for the start times [default='tmin']: tmin
> Enter the column name for the end times [default='tmax']: tmax
> Enter the column name for the tier names [default='tier']: tier
> Enter the column name for the text [default='text']: text

combining multiple TextGrids:
$ python tg_helper.py combine
> Enter the filename (full path) of the table or the TextGrid: /path/to/table.csv
> Enter the output filename (full path): /path/to/output.TextGrid
> Enter the column name for the start times [default='tmin']: tmin
> Enter the column name for the end times [default='tmax']: tmax
> Enter the column name for the tier names [default='tier']: tier
> Enter the column name for the text [default='text']: text
> Enter the filename (full path) of the TextGrid(s) to combine. Enter 'q' to finish: /path/to/tg1.TextGrid
> Enter the filename (full path) of the TextGrid(s) to combine. Enter 'q' to finish: /path/to/tg2.TextGrid
> Enter the filename (full path) of the TextGrid(s) to combine. Enter 'q' to finish: q
"""

# TODO: try merge function from Praat and add an automatic scraping function to merge all TextGrids in a folder or in separate folders to separate TextGrids.
import argparse
import os
import pandas as pd
import parselmouth
from parselmouth.praat import call


class TextGridHandler:
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
    _insert_segment(tg, ntier, nsegment, t1, text) -> parselmouth.TextGrid
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
            # make a table from the TextGrid
            table = call(self.textgrid, "Down to Table", 0, 6, 1, 1)
            call(table, "Save as comma-separated file", "temp.csv")
            self.table = pd.read_csv("temp.csv")  # read the table
            os.remove("temp.csv")  # remove temporary file
            # overwrite the table column names parameters
            self.t0_col = "tmin"
            self.t1_col = "tmax"
            self.tier_col = "tier"
            self.text_col = "text"
            # get tier names
            self.tiers = set(self.table[self.tier_col])
        else:
            self.t0_col = t0_col
            self.t1_col = t1_col
            self.tier_col = tier_col
            self.text_col = text_col
            self._table_handler(filename)
            self.textgrid = self.table_to_textgrid(table=self.table)

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

    def _insert_segment(self, tg, ntier, nsegment, t1, text):
        text = "" if pd.isna(text) or text == "?" else text

        try:
            if t1 < tg.xmax:
                call(
                    tg, "Insert boundary", ntier, t1
                )  # no need to add t0 because it is always == t1(nsegment - 1)
            call(
                tg, "Set interval text", ntier, nsegment, text
            )  # outside if to include text of last segment
        except parselmouth.PraatError:
            # it's a point tier
            call(tg, "Insert point", ntier, t1, text)

        return tg

    def table_to_textgrid(self, table: pd.DataFrame):
        """Converts a table to a TextGrid object.


        Parameters:
        -----------
        table : pandas.DataFrame
            The table to convert to TextGrid.

        Returns:
        --------
        textgrid : parselmouth.TextGrid
            The TextGrid object.
        """
        # init vars
        start = table[self.t0_col].min()
        end = table[self.t1_col].max()
        self.tiers = set(table[self.tier_col])

        # Create a new TextGrid
        tg = parselmouth.TextGrid(
            start_time=start, end_time=end, tier_names=list(self.tiers)
        )

        # loop through the table and add the intervals
        for tier in self.tiers:
            ntier = list(self.tiers).index(tier) + 1
            for nsegment, row in table[table[self.tier_col] == tier].iterrows():
                # insert the segment
                tg = self._insert_segment(
                    tg, ntier, nsegment + 1, row[self.t1_col], row[self.text_col]
                )

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
        t1_col : str, optional
            The name of the column containing the end times of the intervals.
            Default is 'tmax'.
        text_col : str, optional
            The name of the column containing the text.
            Default is 'text'.
        """
        # get the tier number
        ntier = len(self.tiers) + 1

        # check that tier name does not exist already
        if tier_name in self.tiers:
            tier_name = f"{tier_name}_{ntier}"

        self.tiers.add(tier_name)

        # add the tier to the TextGrid
        if tier_table[t0_col][0] == tier_table[t1_col][0]:
            # point tier
            call(self.textgrid, "Insert point tier", ntier, tier_name)
        else:
            # interval tier
            call(self.textgrid, "Insert interval tier", ntier, tier_name)

        # loop through the table and add the intervals
        for nsegment, row in tier_table.iterrows():
            t1 = row[t1_col]
            text = row[text_col]

            # insert the segment
            self.textgrid = self._insert_segment(
                self.textgrid, ntier, nsegment + 1, t1, text
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
    ref_tg = TextGridHandler(
        filename=textgrids.pop(0),
        t0_col=t0_col,
        t1_col=t1_col,
        tier_col=tier_col,
        text_col=text_col,
    )  # reference textgrid
    to_add_tg = [
        TextGridHandler(
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
        for tier_name in tg.tiers:
            tier_table = tg.table[
                tg.table[tier_col] == tier_name
            ].reset_index()  # extract only tier rows
            ref_tg.add_tier(
                tier_name, tier_table, tg.t0_col, tg.t1_col, tg.text_col
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
    tgHelper = TextGridHandler(filename, t0_col, t1_col, tier_col, text_col)
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
    filename = str(
        input("Enter the filename (full path) of the table or the TextGrid: ")
    )
    iMax = 5  # max tries
    while iMax > 0:
        output_filename = str(input("Enter the output filename (full path): "))
        if output_filename == "":
            print("Output filename cannot be empty. Try again.")
            iMax -= 1
            continue
        elif os.path.exists(output_filename):
            if input("File already exists. Overwrite? (y/n) ") == "y":
                break
        else:
            break
    if iMax == 0:
        print("Too many tries. Exiting.")
        return
    t0_col = str(
        input("Enter the column name for the start times [default='tmin']: ") or "tmin"
    )
    t1_col = str(
        input("Enter the column name for the end times [default='tmax']: ") or "tmax"
    )
    tier_col = str(
        input("Enter the column name for the tier names [default='tier']: ") or "tier"
    )
    text_col = str(
        input("Enter the column name for the text [default='text']: ") or "text"
    )

    if parsed_args.function == "convert":
        convert_to_textgrid(
            filename, output_filename, t0_col, t1_col, tier_col, text_col
        )
    else:  # combine
        textgrids = [filename]
        while True:
            tg = str(
                input(
                    "Enter the filename (full path) of the TextGrid(s) to combine. Enter 'q' to finish: "
                )
            )
            if tg == "q":
                break
            textgrids.append(tg)
        combine_textgrids(
            textgrids, output_filename, t0_col, t1_col, tier_col, text_col
        )

    print("Done.\nYour new TextGrid is saved as:", output_filename)


if __name__ == "__main__":
    # main()

    # DEBUGGING ################################################################
    os.chdir(
        os.path.abspath(
            "C:\\Users\\adelu\\Documents\\projects\\programming\\myscripts\\Python\\sound_processing"
        )
    )
    output_filename = "test_combined.TextGrid"
    textgrids = ["test_tg.TextGrid", "testwithpoint_tg.TextGrid"]
    combine_textgrids(textgrids, output_filename)
