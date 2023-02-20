# Using CV segments TextGrids, returns a table with the segment type, the start and end time
# Alessandro De Luca - 12/2022

inputDir$ = ""
outputDir$ = ""

fileNames$# = fileNames$#(inputDir$ + "*.TextGrid")

for iFile to size(fileNames$#)
    Read from file: inputDir$ + fileNames$# [iFile]
    tg = selected("TextGrid")
    filename$ = selected$("TextGrid")

    # Get tmin, tmax for tiers 
    Down to Table: 0, 6, 1, 0
    
    Extract rows where column (text): "tier", "is equal to", "cvIntervals"; get only complete intevals
    Remove column: "tier"
    Set column label (label): "text", "segment"

    Save as comma-separated file: outputDir$ + filename$ + ".csv"
    
    select all
    Remove
endfor
