sound = selected("Sound")
sound$ = selected$("Sound")
sf = Get sampling frequency
duration_tot = Get total duration

noprogress To Harmonicity (cc): 0.01, 75, 0.01, 1.0
harm = selected("Harmonicity")
matrix = To Matrix
harm.sound = To Sound
resamp = Resample: sf, 1
Rename: "resamp"
Formula: ~if self < 4.5 then 0 else 1 fi
selectObject: sound
harmOnly = Copy: sound$+"_harmonicPartsOnly"
Formula: ~self*Sound_resamp[]

selectObject: harmOnly
sound_trimmed = Trim silences: 0.0001, 0, 250, 0.0, -25.0, 0.0001, 0.0001, 1, "silence"
selectObject: sound_trimmed
duration_harmOnly = Get total duration
noprogress To Harmonicity (cc): 0.01, 75, 0.01, 1.0
harm_onlyPeaks = selected("Harmonicity")
meanHNR = Get mean: 0, 0
stdHNR = Get standard deviation: 0, 0
maxHNR = Get maximum: 0.0, 0.0, "parabolic"
ratio_duration = duration_harmOnly / duration_tot