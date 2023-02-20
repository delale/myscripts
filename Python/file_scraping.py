# Alessandro De Luca, May 2021

"""
This script is made to copy files named with a certain pattern (usually individual
name + some more information).

3 functions are defined:
    - find_files: finds the filenames with the pattern and returns their path
        in a list
    - copy_files: copies the files to the target directory creating the new
        subdirectory if it doesn't exist yet
    - patterns: this is a specific function for a list of patterns to
        search (e.g. individuals needed for specific project). The function
        takes as input a .csv with 1 column containing the patterns list, padds
        the patterns with * so that all files containing the pattern are returned
        when running find_files, and returns a python set (exclusively iterable
        object) containing the unique patterns.

The script also creates a log file with information, files found, files copied,
and possibe errors.

USE:
    When ran as main the script automatically does everything as in the sample code.
    To run: in a terminal/cmd/powershell window move to the directory where the 
        script is stored and then run python file_scraping.py (bash) or 
        .\\file_scraping.py (powershell/cmd).
    The script can also be imported into any other python project to use its 
        functions.

WARNINGS:
    When ran directly please modify the search paths lists, the path to the 
        patterns/individuals code .csv file, and the target path.
    I advise to do this modifications in the main() function:
        as this way the automatic file scraping won't run when importing the script
        into another python project.
"""


import os
import glob
import shutil as sh
import pandas as pd
import logging


def find_files(pattern, search_path):
    """
    Finds files having a certain pattern in their filename in the search directory.

    Parameters:
    [path subdirectory delimiter "\\" Windows or "/" Linux/Mac]
    pattern: [str] to be specified as pattern already (e.g. *individual*")
    search path: [str] path where to search with "\\" at the end

    Returns:
    file_list: [list] list of absolute paths to the files matching the pattern 
    """

    # find file -> list of paths
    file_list = glob.glob(search_path+pattern, recursive=True)

    if len(file_list) == 0:
        return []
    else:
        return file_list


def copy_files(original_path, target_path):
    """
    Copies files to target directory creating new subdirectory if it does not
    exist yet.

    Parameters:
    [path subdirectory delimiter "\\" Windows or "/" Linux/Mac]
    original_path: [str] complete path to file to copy (including filename.extension)
    target_path: [str] complete path to copy the file to (including filename.extension)
    """

    subdir = "\\".join(target_path.split("\\")[:-1])

    # creates the new subdirectory (+ intermediates) if it does not exist already
    try:
        os.makedirs(subdir)
    except FileExistsError:
        pass

    sh.copyfile(original_path, target_path)


def patterns(path_to_data):
    """
    Padds patterns in a .csv file and then returns them in a set.

    Parameters:
    [path subdirectory delimiter "\\" Windows or "/" Linux/Mac]
    path_to_data: [str] path to the file containing the individual codes (must be .csv)

    Returns:
    [set]: set of patterns after padding
    """

    ind_data = pd.read_csv(path_to_data)

    # if more than just one col containing the codes must specify col num.
    # creates a set in case of duplicates
    return set(["*"+code+"*" for code in ind_data.iloc[:, 0].tolist()])


def main():

    # log file config
    os.chdir("working directory for the log file")

    logging.basicConfig(
        filename="file_scraping.log",
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s"
    )

    # selection of paths to search in (** := search in all subdirectories)
    paths_list = ["search path"]

    # individuals' codes list
    pattern_list = patterns(path_to_data="path to patterns list")

    files = []

    for path in paths_list:

        for p in pattern_list:

            try:
                # gathers all files in one list
                files = files + find_files(pattern=p, search_path=path)
                logging.info(
                    "Successfully searched for {0} in {1}".format(p, path))
            except Exception:
                logging.exception(
                    "While looking for {0} in {1}".format(p, path))

    logging.info("FINISHED SEARCHING")
    logging.info("BEGIN COPYING")

    for name in files:

        # creeates target path (first part is own path, second is part of the original)
        target = "target path"

        try:
            copy_files(original_path=name, target_path=target)
            logging.info("Successfully copied {}".format(name))
        except Exception:
            logging.exception("Unuccessfully copied {}".format(name))

    logging.info("FINISHED COPYING FILES")
    logging.info("DONE")
    print("DONE")


if __name__ == "__main__":
    main()
