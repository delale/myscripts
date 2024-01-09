#!/bin/bash

directory=$1
old_word=$2
new_word=$3

rename_files() {
    for file in "$directory"/*"$old_word"*; do
        if [ -f "$file" ]; then
            new_name=$(echo "$file" | sed "s/$old_word/$new_word/")
            mv "$file" "$new_name"
            echo "Renamed: $file -> $new_name"
        fi
    done

    for dir in "$directory"/*/; do
        if [ -d "$dir" ]; then
            (cd "$dir" && rename_files)
        fi
    done
}

rename_files