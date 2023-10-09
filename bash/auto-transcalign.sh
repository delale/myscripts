#!/usr/bin/env bash

#####################################################################
# Bash script to use automatically:                                 #
#   1. transcribe audio files in a directory using whisper.cpp      #
#   2. force-align using montreal-forced-aligner                    #
#                                                                   #
# Alessandro De Luca - 10.2023                                      #
#####################################################################

if [ "$#" -eq 0]; then
    echo "Usage: '$0' <input_directory> <output_directory>"
    exit 1
fi

in_dir="$1"
out_dir="$2"
if [ ! -d "$in_dir" ]; then
    echo "'$in_dir' not a directory"
    exit 1
fi
if [ ! -d "$out_dir" ]; then
    echo "'$out_dir' not a directory"
    exit 1
fi

# conda activate align
conda activate soundprocessing  # change this to env where whisper-openai and mfa are installed

mfa model download acoustic english_mfa
mfa model download dictionary english_us_mfa

whisper "$in_dir"/* --model large-v2 --verbose False --output_format txt
mfa align "$in_dir" english_us_mfa english_mfa "$out_dir" --textgrid_cleanup --include_original_text