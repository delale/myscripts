# Praat script to turn MFCC objects into csv tables
# Takes as input a directory, selects all mfcc objects and saves them as csv
# tables in the output directory
# Alessandro De Luca - 12/2022

inputDir$ = "~/Documents/test/input/"
outputDir$ = "~/Documents/test/output/"

fileNames$# = fileNames$#(inputDir$+"*.MFCC")

for iFile to size(fileNames$#)
   Read from file: inputDir$ + fileNames$# [iFile]
   mfccObj = selected("MFCC")
   name$ = selected$("MFCC")

   To Matrix
   Transpose
   Save as headerless spreadsheet file: outputDir$ + name$ + ".txt"; # tab separated file

   select all
   Remove
endfor