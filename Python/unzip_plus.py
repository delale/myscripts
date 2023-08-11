"""Unzipping multiple complex archives from directory, keeping only wanted parts of archive.
Complex archives: archives containing a subfolder tree.
The script allows to specify an input_directory containing the .zip archives, an output_directory 
to write the extracted files to and a list of files to remove (remove).
You can also run a test by specifying --run_test 1 from the CLI, as long as the in_test/ directory 
containing at least one .zip archive exists in the working directory.

For files to ignore during extraction (arguments to --remove) you can specify directory names without 
path separators (\ or /), specific files, and file types by prepending them with '.' (e.g. .mp3).

The script also writes to the output_directory a log file named unzip_plus.log

Example usage:
    python3 unzip_plus --input_directory my/path/input_directory --output_directory my/path/output_directory --remove directory filename file.example .extension 

    to run test script:
    python3 unzip_plus --run_test 1
"""

import argparse
import logging
import os
import zipfile
import shutil

def extract_and_filter_zips(input_directory: str, output_directory: str, to_remove: list) -> None:
    """Extracts zip archives to an output directory from an input directory ignoring 
    filenames, directories, specific files, and extensions specified in the to_remove list.

    Args:
        input_directory: Directory containing the .zip archives to extract.
        output_directory: Directory to write the extracted files to.
        to_remove: List of filenames, directories, specific files, and extensions to 
            ignore during extraction (i.e. to not extract).
    """
    # ensure correct paths
    if not os.path.isdir(input_directory):
        raise ValueError(f"{input_directory} does not exist")
    if not os.path.isdir(os.path.dirname(output_directory)):
        raise ValueError(
            f"{os.path.dirname(output_directory)} " +\
                "does not exist. Nowhere to create output directory."
            )

    # Make to remove a list
    if type(to_remove) is str:
        to_remove = [to_remove]
    elif type(to_remove) is not list:
        raise ValueError("to_remove should be of type str or list.")
    else:
        # check that all items of to_remove are strings
        for i in to_remove:
            if type(i) is not str:
                raise ValueError("All items in to_remove should be strings.")
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Init logger
    logging.basicConfig(
        filename=os.path.join(output_directory, "unzip_plus.log"),
        encoding='utf-8', level=logging.DEBUG, filemode='w'
    )
    logging.info(
        f" unzip_plus.py called from {os.getcwd()} with parameters:\n" +\
        f"\t- input_directory={input_directory}\n" +\
        f"\t- output_directory={output_directory}\n" +\
        f"\t- remove={to_remove}\n" + "-"*15 + "\n\n"
        )

    # Iterate through each file in the input directory
    for filename in os.listdir(input_directory):
        filepath = os.path.join(input_directory, filename)

        # Check if the file is a zip archive
        if filename.endswith(".zip"):
            try:
                logging.info(f" Extracting {filename}...")
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    
                    # Extract each item in the archive
                    for item in zip_ref.infolist():
                        if os.path.dirname(item.filename).split('/')[-1] not in to_remove and\
                            os.path.basename(item.filename) not in to_remove and\
                                os.path.splitext(item.filename)[-1] not in to_remove:
                            if not (
                                os.path.isfile(os.path.join(output_directory, item.filename)) or\
                                    os.path.isdir(os.path.join(output_directory, item.filename))
                            ):
                                # Extract the item if not in to_remove
                                zip_ref.extract(item, output_directory)
                                logging.info(
                                    f" Extracted {item.filename} \n\tto " +\
                                    f"{os.path.join(output_directory, item.filename)}"
                                    )
                            else:
                                logging.info(
                                    f"{os.path.join(output_directory, item.filename)} already exists."
                                    )

                        ## Deprecated code by GPT-3: does not work as intended
                        # # Get the extracted item's path
                        # extracted_path = os.path.join(output_directory, item.filename)
                        
                        
                        # # Remove the to_remove subfolder(s) if it exists
                        # for subfolder in to_remove:
                        #     remove_path = os.path.join(extracted_path, subfolder)
                        #     if os.path.exists(remove_path) and os.path.isdir(remove_path):
                        #         shutil.rmtree(remove_path)

                        ## Only needed if you want to store each subfolder file outside of the subfolder.  
                        # # Move the extracted content to the final destination
                        # extracted_items = os.listdir(extracted_path)
                        # for extracted_item in extracted_items:
                        #     extracted_item_path = os.path.join(extracted_path, extracted_item)
                        #     shutil.move(extracted_item_path, output_directory)
                        # os.rmdir(extracted_path)
                    
                    logging.info(f" ...Done extracting {filename}\n")

            except zipfile.LargeZipFile as zip_error:
                if isinstance(zip_error, zipfile.BadZipFile):
                    print(f"BadZipFile error for file:\n\t{filepath}\n")
                    # logging.error(f"BadZipFile error for file:\n\t{filepath}\n")
                    raise zip_error
                else:
                    raise zip_error
        

def test() -> None:
    # Test usage:
    input_directory = os.path.join(os.getcwd(), "in_test")
    output_directory = os.path.join(os.getcwd(), "out_test")
    to_remove = ["raw", "audio_video_features.csv", "transcription", ".mp4", ".png"]
    extract_and_filter_zips(input_directory, output_directory, to_remove)

def main(input_directory, output_directory, run_test, remove) -> None:
    if run_test:
        # run the test
        test()
    else:
        if input_directory == os.getcwd():
            x = input(
                f"""Warning: No argument for --input_directory.
                The input directory used will be {input_directory}. Do you confirm? (y or [n])"""
                )
            if x == 'n' or x == '':
                print("Aborted.")
                return None
            
        if output_directory == os.path.join(os.getcwd(), 'output'):
            x = input(
                f"""Warning: No argument for --output_directory.
                The input directory used will be {output_directory}. Do you confirm? (y or [n])"""
                )
            if x == 'n' or x == '':
                print("Aborted.")
                return None

        # run the script
        extract_and_filter_zips(
            input_directory=input_directory, output_directory=output_directory,
            to_remove=remove
        )

if __name__ == "__main__":
    # CLI argument parser
    parser = argparse.ArgumentParser(description="Pass arguments from the CLI.")
    parser.add_argument(
        "--input_directory", type=str, nargs='?', default=os.getcwd(), const=os.getcwd(),
        help="Input directory containing the archive(s)."
        )
    parser.add_argument(
        "--output_directory", type=str, nargs='?', default=os.path.join(os.getcwd(), 'output'), 
        const=os.path.join(os.getcwd(), 'output'),
        help="Output directory where to extract the files."
        )
    parser.add_argument(
        "--run_test", type=int, default=0, const=0, nargs='?',
        help="Run test() function. Default=0 -> don't run test()."
    )
    parser.add_argument(
        "--remove", nargs='*', default=[],
        help="Subfolders to remove after decompression."
    )
    args = parser.parse_args()

    # run
    main(
        input_directory=args.input_directory, output_directory=args.output_directory,
        run_test=args.run_test, remove=args.remove
        )