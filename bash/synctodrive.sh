#!/usr/bin/ bash

# personal script to sync to ssd #

default_output_directory="/Volumes/delT7 - 1TB/"
echo "default_output_directory: $default_output_directory"

# if no output directory is specified, use the default
if [ "$#" -eq 0 ]; then
    output_directory="$default_output_directory"
else
    output_directory="$1"
fi

if [ ! -d "$output_directory" ]; then
    echo "Error: '$output_directory' is not a directory"
    exit 1
fi

echo "Moving to ~/Documents"
cd ~/Documents
pwd

echo "Starting sync to $output_directory"
rsync -rlptP --stats --exclude='00_tmp' 0* NotAles $"output_directory"
echo "Sync complete"

