rDir$="temp/"
wDir$="temp2/"

files$# = fileNames$#(rDir$+"*.wav")
for iFile to size(files$#)

	sound = Read from file: rDir$+files$#[iFile]
	sound$ = selected$("Sound")
	noprogress To Pitch: 0, 75, 500
	pitch = selected("Pitch")
	pp = To PointProcess
	tg = To TextGrid (vuv): 0.02, 0.01
	nInt = Get number of intervals: 1
	counter=0
	for iInt to nInt
	
		selectObject: tg
		label$ = Get label of interval: 1, iInt
		if label$ = "V"
			start = Get start point: 1, iInt
			end = Get end point: 1, iInt
			selectObject: sound
			start = Get nearest zero crossing: 1, start
			end = Get nearest zero crossing: 1, end
			counter+=1
			part[counter] = Extract part: start, end, "rectangular", 1, 0
		endif

	endfor

	selectObject: part[1]	
	for iCounter from 2 to counter
		plusObject: part[iCounter]
	endfor
	all = Concatenate
	Save as WAV file: wDir$+sound$+".wav"

	for iCounter to counter
		removeObject: part[iCounter]
	endfor

	removeObject: pitch, pp, tg

endfor


