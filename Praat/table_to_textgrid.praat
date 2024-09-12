###############################################################################
# Convert a table to a TextGrid object
# The table should have the following columns:
# - tier: the name of the tier
# - tmin: the start time of the interval
# - tmax: the end time of the interval
# - text: the text of the interval
###############################################################################
table = selected ()
table$ = selected$ ()
start = Get minimum: "tmin"
end = Get maximum: "tmax"
Sort rows: "tier"; # sort the rows by the tier name
cur_tier$ = Get value: 1, "tier"
cur_tier = 1
t0 = Get value: 1, "tmin"
t1 = Get value: 1, "tmax"
is_point = t0 == t1

# Create a new TextGrid object
if is_point
    tg = Create TextGrid: start, end, cur_tier$, cur_tier$
else
    tg = Create TextGrid: start, end, firtTier$,
endif
Rename: table$

# Add the tiers
selectObject: table
nRows = Get number of rows
for iRow to nRows
    selectObject: table
    t0 = Get value: iRow, "tmin"
    t1 = Get value: iRow, "tmax"
    tier$ = Get value: iRow, "tier"
    text$ = Get value: iRow, "text"

    selectObject: tg
    # check for new tier
    if tier$ != cur_tier$
        # Add new tier
        cur_tier$ = tier$
        cur_tier = cur_tier + 1
        is_point = t0 == t1
        if is_point
            Insert point tier: cur_tier, cur_tier$
        else
            Insert interval tier: cur_tier, cur_tier$
        endif
    endif

    # Add the interval/point
    if is_point
        Insert point: cur_tier, t0, text$
    else
        if t1 < end
          Insert boundary: cur_tier, t1
        endif
        iInterval = Get interval at time: cur_tier, t0
        Set interval text: cur_tier, iInterval, text$
    endif
endfor