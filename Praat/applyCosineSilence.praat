###
# Cleaning script to reverse hann window silent sections.
# Alsseandro De Luca (alessandro.deluca@uzh.ch) + Volker Dellwo (volker.dellwo@uzh.ch)

# Description: 
# This script modifies a sound by applying a cosine function to the signal
# in silent intervals (as selected by automatic VAD with manual check).
# If the first and/or last intervals are silent, only a half period or the cosine
# is used; respectively first half (0 -> pi) and second half (pi -> 2pi).
#
# INPUT:
#    - A Sound.
# 
# OUTPUT:
#	 - A modified sound with VAD TextGrid.
#
# INSTRUCTIONS: 
#    - Select a Sound.
#    - Execute the script.
#	 - Check VAD TextGrid (opens automatically) and then click Finished when done.
#	 	-> only modifications on the first tier are used.
###

# Construct objects

	sound = selected("Sound")
	sound$ = selected$("Sound")
	originalEndT = Get end time
	sound_new = Copy: sound$+"_mod"

# Voice activity detection (vad): 

	vad1 = To TextGrid (voice activity): 0, 0.05, 0.005, 200, 6000, -10.0, -15.0, 0.05, 0.01, "s", "v"
	Remove tier: 2
	Remove tier: 3

	# add manual check for VAD
	beginPause: "Check the VAD intervals"
		selectObject: sound, vad1
		Edit
	endPause: "Finish", 1
	
	# VAD down to table
	selectObject: vad1
	vad2 = Down to Table: 0, 3, 1, 0
	vad3 = Extract rows where: ~self$["tier"]="union" and self$["text"]="s"

# Check that first and last intervals are voiced
	selectObject: vad1
	nInt = Get number of intervals: 1
	first_interval$ = Get label of interval: 1, 1
	last_interval$ = Get label of interval: 1, nInt

# Apply silence to pauses with cosine weight: 

	selectObject: sound_new
	for iInt to object[vad3].nrow
		# define variables:
		startT = object[vad3, iInt, "tmin"]
		endT = object[vad3, iInt, "tmax"]
		pT = endT-startT; period duration of cosine
		f = 1/pT; frequency of cosine
		psF = startT/pT-floor(startT/pT); phase-shift factor
		psPI = psF*2*pi; phase-shift in pi

		# appy cosine silence:
		if first_interval$="s" and iInt=1 
			Formula (part): startT, endT, 1, 1, ~ self * (1/2*cos((2*pi*f*x-psPI)/2 + pi)+0.5)
		else
			if last_interval$="s" and iInt=object[vad3].nrow
				Formula (part): startT, endT, 1, 1, ~ self * (1/2*cos((2*pi*f*x-psPI)/2 - pi)+0.5)
			else
				Formula (part): startT, endT, 1, 1, ~ self * (1/2*cos(2*pi*f*x-psPI)+0.5)
			endif
		endif
	endfor

# clean up:
	removeObject: vad2, vad3
	selectObject: sound_new, vad1
	Edit
