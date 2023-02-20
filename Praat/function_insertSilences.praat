### insertSilences.praat #################
#
# Praat Script for Praat software (www.praat.org)
# Written by Volker Dellwo (volker.dellwo@uzh.ch)
#
# Description: 
# This script splits a sound at fixed duration (speechDuration) and
# inserts silences of a fixed duration (silenceDuration) between each speech interval. 
# The script can be used to replicate some of the stimuli in 
# Ghitza, O. and Greenberg, S. (2009) On the Possible Role of Brain Rhythms in Speech
# Perception, in: Phonetica (66, 1-2), p.113-126.  
#
# INPUT:
#    - A Sound (ideally chose a sentence utterance)
# 
# OUTPUT:
#		 - A new Sound with a corresponding TextGrid. The sound has been changed in 
#			 duration by durationFactor (typically between 0.02 and 0.12 seconds). And 
#			 contains the inserted silences of 'silenceDuration' duration at 
#			 'speechDuration' intervals.  
# 
# INSTRUCTIONS: 
#    - Select a Sound.
#    - Execute the script. 
#
# Comments: 
#		 - The new Sound and TextGrid are selected when the script finishes. The names
#			 include information about the durational chance (duratio), the speech interval 
#			 duration (speech) and the silence interval duration (sil); all time information 
#			 is in miliseconds. 
#
# HISTORY 
#    8.6.2022: created
#
###

form Insert silences...
	real durationFactor 1/3
	real silenceDuration 0.06
	real speechDuration 0.04
	boolean Leave_shortened_version 0
endform

original = selected("Sound")
name$ = selected$("Sound")

sound = Lengthen (overlap-add): 75, 600, durationFactor
sf = Get sampling frequency
tg = To TextGrid: "silenceIntervals", "none"

boundary= speechDuration
repeat
	
	Insert boundary: 1, boundary
	boundary+=speechDuration

until boundary>=object[sound].xmax 

nInterval = Get number of intervals: 1
for iInt to nInterval
	
	selectObject: tg
	start = Get start point: 1, iInt
	end = Get end point: 1, iInt
	
	selectObject: sound
	start = Get nearest zero crossing: start
	end = Get nearest zero crossing: end
	part[iInt] = Extract part: start, end, "rectangular", 1, 0
	if iInt<nInterval
		sil[iInt] = Create Sound from formula: "sil", 1, 0, silenceDuration, sf, ~0
	endif

endfor

selectObject: part[1], sil[1]
for i from 2 to nInterval-1
	plusObject: part[i], sil[i]
endfor
plusObject: part[nInterval]
Concatenate recoverably
concat.s = selected("Sound")
concat.tg = selected("TextGrid")

for i to nInterval-1
	removeObject: part[i], sil[i]
endfor
removeObject: part[i]
removeObject: tg

selectObject: sound
Rename: name$+"_duration"+fixed$(durationFactor*1000,0)
selectObject: concat.s
Rename: name$+"_duration"+fixed$(durationFactor*1000,0)+"_speech"+fixed$(speechDuration*1000,0)+"_sil"+fixed$(silenceDuration*1000,0)
selectObject: concat.tg
Rename: name$+"_duration"+fixed$(durationFactor*1000,0)+"_speech"+fixed$(speechDuration*1000,0)+"_sil"+fixed$(silenceDuration*1000,0)

nInt = Get number of intervals: 1
c=0
for iInt to nInt
	label$ = Get label of interval: 1, iInt
	if label$!="sil"
		c+=1
		Set interval text: 1, iInt, string$(c)
	endif
endfor

if leave_shortened_version=0
	removeObject: sound
endif

selectObject: concat.s, concat.tg








