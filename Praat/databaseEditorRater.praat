######################################################################################
# Praat script to rate sequentially view, edit, (and rate) sound files in a directory.                                                                   
                                                                    
# Usage:                                                                       
# 1. Run the script from Praat                                                 
# 2. Specify the input directory where the sound files are located.
# 3. Specify the output directory where the sound files will be saved.
# 4. Specify if you would like to only edit the files.
# 5. View & edit the sound in the automatically opened window.
# 6. (Optional) Rate the quality of the recording.
# 7. (Optional) Specify a new file name. Click continue to move on to the next file.

# Alessandro De Luca - 2024                                                    
#####################################################################################

# Get lists of files in the directory
form databaseExplorerRater...
    comment Specify input directory and (optional) output directory. You can also specify if you would like to only edit the sound files and not rate them or extract metadata.
    folder inDir /Users/aledel/Documents/
    folder outDir /Users/aledel/Documents/
    boolean editOnly 0
	choice Sampling_frequency_(Hz) 7
		button 8000
		button 10000
		button 16000
		button 22050
		button 44100
		button 48000
		button original
    optionmenu quantization 1
        option 16
        option 24
        option 32
endform

# Create a table to store the results
if not editOnly
	Create Table with column names: "rating", 0, "source_file filename tot_duration sampling_freq n_channels VAD_duration quality"
	quality = 1
endif

# Get files
listFiles = Create Strings as file list: "files", inDir$ + "/*.wav"
nFiles = Get number of strings

clearinfo
# For each file in the directory
for iFile to nFiles
    # Read the audio file
    selectObject: "Strings files"
    filename$ = Get string: iFile
	appendInfoLine: "Reading: " + filename$
    sound = Read from file: inDir$ + "/" + filename$
	fileID$ = left$ (filename$, length (filename$) - 4)

    # Display the audio file (waveform + spectrogram)
    selectObject: sound

	# Resample (if selected)
	if not sampling_frequency == 7
		sound = Resample: number(sampling_frequency$), 50
		selectObject: sound
	endif
    Edit
    if editOnly
        # editor form
        beginPause: "Done"
            comment: "Click Continue when you are finished editing."
            word: "New file name", filename$
        endPause: "Continue", 1
    else
        # quality rating form
        beginPause: "Rate quality"
            comment: "Rate the quality of the soundfile and when finished click Continue"
            word: "New file name", filename$
            optionMenu: "Quality", quality
                option: "excellent"
                option: "good"
                option: "fair"
                option: "poor"
                option: "worst"
        endPause: "Continue", 1
    endif
    # close editor
    editor: sound
        Close

    # Correctly format the new file name
    has_extension = endsWith (new_file_name$, ".wav")
    if not has_extension
        new_file_name$ = new_file_name$ + ".wav"
    endif
    
    # Extract file information
    if not editOnly
		appendInfoLine: "Extracting sound info..."
        selectObject: sound
        duration = Get total duration
        sr = Get sampling frequency
        nChannels = Get number of channels

        # Extract VAD speech duration
        tg = To TextGrid (speech activity): 0.0, 0.3, 0.1, 70.0, 6000.0, -10.0, -35.0, 0.1, 0.1, "sil", "v"
        selectObject: tg
        vadspeechDur = Get total duration of intervals where: 1, "is equal to", "v"
        appendInfoLine: "dur: ", duration, "; sr: ", sr, "; nChannels: ", nChannels, "; vadspeechDur: ", vadspeechDur
        appendInfoLine: "Finished"
    endif
	
    # Store variables in table
    if not editOnly
		appendInfoLine: "Updating table..."
        selectObject: "Table rating"
        nRows = Get number of rows
        Append row
        Set string value: nRows + 1, "source_file", filename$
        Set string value: nRows + 1, "filename", new_file_name$
        Set numeric value: nRows + 1, "tot_duration", duration
        Set numeric value: nRows + 1, "sampling_freq", sr
        Set numeric value: nRows + 1, "n_channels", nChannels
        Set numeric value: nRows + 1, "VAD_duration", vadspeechDur
        Set string value: nRows + 1, "quality", quality$
        appendInfoLine: "Finished"
    endif

    # Save the audio file
    appendInfoLine: "Saving sound... "
    selectObject: sound
    if number(quantization$) == 24
        Save as 24-bit WAV file: outDir$ + "/" + new_file_name$
    elsif number(quantization$) == 32
        Save as 32-bit WAV file: outDir$ + "/" + new_file_name$
    else
        Save as WAV file: outDir$ + "/" + new_file_name$
    endif

	appendInfoLine: "Saved: " + new_file_name$

    # Remove objects
    selectObject: sound
	if not editOnly
    		plusObject: tg
	endif
    Remove

    appendInfoLine: ""
endfor

appendInfoLine: "DONE"

if not editOnly
    # Save the table
    appendInfoLine: "Saving table..."
    selectObject: "Table rating"
    Save as comma-separated file: outDir$ + "/soundDirInfo.csv"
	appendInfoLine: "Saved table: " + outDir$ + "/soundDirInfo.csv"
endif

# Close all objects
select all
Remove