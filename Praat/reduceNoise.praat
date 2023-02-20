# Cleaning script that only filters calls
# HISTORY:
#	original: unknown from UZH IEU Communication and Cognition in Social Mammals Group
#	12.7.2022: modified by Alessandro De Luca (alessandro.deluca@uzh.ch)
#		- added form for selection of folders

form Cleaning...
	folder inpDIR /home/aledel/Documents/meerkat_brain_rythm_and_communication/audio_files/original
	folder outDIR /home/aledel/Documents/meerkat_brain_rythm_and_communication/audio_files/original_clean
endform

Create Strings as file list... fileList 'inpDIR$'/*.wav
counter = Get number of strings
clearinfo
print 'counter''newline$'

for i to counter
	select Strings fileList
		fileName$ = Get string: 'i'
		print 'fileName$''newline$'

		Read from file... 'inpDIR$'/'fileName$'
		initialSound$ = selected$ ("Sound")

		Reduce noise: 0.0, 0.15, 0.025, 70.0, 22050.0, 40.0, -15.0, "spectral-subtraction"
		Rename: initialSound$

		Save as WAV file... 'outDIR$'/'initialSound$'.wav
		select all
		minus Strings fileList
		Remove
endfor

select all
Remove