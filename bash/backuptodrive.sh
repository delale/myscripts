#!/usr/bin/ bash

# personal script to backup to ssd #
 
default_output_directory="/Volumes/delT7 - 1TB/backups"
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

echo "Starting backup to $output_directory"
rsync -rlptbP --stats 01_current_projects 00_admin "$output_directory"
echo "Backup complete"

