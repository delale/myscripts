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
#	 - Open a Sound and its TextGrid in Praat
#    - Select the Sound.
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
#	 1.9.2022: modified by Alessandro De Luca (alessandro.deluca@ieu.uzh.ch) & V. Dellwo to work with Voiced-Silent TextGrids
#			   	to insert silences in the middle of silent intervals.
###

form Insert silences...
	real durationFactor 1/3
	real silenceDuration 0.06
	real minPitch 230
	real maxPitch 800
	boolean leave_shortened_version 0
endform

original = selected("Sound")
name$ = selected$("Sound")

sound = Lengthen (overlap-add): minPitch, maxPitch, durationFactor
sf = Get sampling frequency

selectObject: "TextGrid "+name$
tg = Copy: name$
Scale times by: durationFactor
table1 = Down to Table: 0, 6, 1, 0
table2 = Extract rows where: ~self$["tier"]="union"
Append column: "centre"
Formula: "centre", ~self["tmin"]+(self["tmax"]-self["tmin"])/2

start = 1
end = object[table2].nrow
if object$[table2, 1, "text"]="s"
	start = 2
endif
if object$[table2, end, "text"] = "s"
	end-=1
endif

counter=0
startT=0
for iSil from start to end

	if object$[table2, iSil, "text"]="s" and iSil<end
		selectObject: sound
		counter+=1
		part[counter]=Extract part: startT, object[table2, iSil, "centre"], "Rectangular", 1, 0
		sil[counter]=Create Sound from formula: "sil", 1, 0, silenceDuration, sf, ~0
		startT = object[table2, iSil, "centre"]
	elsif iSil = end
		selectObject: sound
		counter+=1
		part[counter]=Extract part: startT, object[sound].xmax, "Rectangular", 1, 0
	endif
endfor

selectObject: part[1]
for iO to counter-1
	plusObject: part[iO], sil[iO]
endfor
plusObject: part[counter]
all = Concatenate

for iO to counter-1
	removeObject: part[iO], sil[iO]
endfor
removeObject: part[counter], table1, table2

if leave_shortened_version=1
	selectObject: sound
	Rename: name$+"_duration"+fixed$(durationFactor*1000,0)
else
	removeObject: sound, tg
endif

selectObject: all
Rename: name$+"_duration"+fixed$(durationFactor*1000,0)+"_sil"+fixed$(silenceDuration*1000,0)