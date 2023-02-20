rm(list = ls())

# working directory
setwd("C:/Users/adelu/Documents/UZH/Thesis/audio")

library(tidyverse)

# choose annotation file
fyle <- file.choose()

# annotation df
annot_dd <- read.delim(fyle, sep = "\t")
colnames(annot_dd)[1] <- "Name"

# file name
fyle_name <- str_split(fyle, "\\\\")[[1]][9]
str_sub(fyle_name, start = -4) <- ""

# metadata df
meta_dd <- read.csv(
    "audio_metadata.csv",
    stringsAsFactors = FALSE,
    colClasses = c(
        "character", "factor", "integer", "numeric", "Date",
        "character", "character", "factor",
        "character", "character", "character"
    )
)

# lifehistory info df
lh <- read.csv("C:/Users/adelu/Documents/UZH/Thesis/individual_selection/selection_dfs/sel_ind_info.csv")

# to add to metadata df
newdd <- data.frame(matrix(nrow = nrow(annot_dd), ncol = ncol(meta_dd)))
colnames(newdd) <- colnames(meta_dd)

# gather general info
print(paste("Filename:", fyle_name))
rec_date <- readline(prompt = "rec date: ")
rec_date <- as.Date(rec_date, format = "%d/%m/%Y")
code <- readline(prompt = "individual code: ")
source_fyle <- paste(fyle_name, "WAV", sep = ".")
group_name <- readline(prompt = "Group Name: ")
bd <- lh %>%
    filter(Code == code) %>%
    select(BirthDate) %>%
    as.character() %>%
    as.Date()
age_d <- as.numeric(rec_date - bd)
age_y <- age_d / 365
id <- lh %>%
    filter(Code == code) %>%
    select(IndividID) %>%
    as.numeric()
sex <- lh %>%
    filter(Code == code) %>%
    select(Sex) %>%
    as.character()

# creates call file names
call_fyle <- c()

for (i in 1:nrow(annot_dd)) {
    if (i < 10) {
        tmp <- paste(fyle_name, "_AD_0", as.character(i), ".WAV", sep = "")
    } else {
        tmp <- paste(fyle_name, "_AD_", as.character(i), ".WAV", sep = "")
    }

    call_fyle <- append(call_fyle, tmp)
}

# gathers call type from annotation
call_type <- apply(annot_dd["Name"], 1, function(x) {
    str_sub(x, end = 4) <- ""
    return(x)
})

newdd["GroupName"] <- rep(group_name, nrow(newdd))
newdd["Sex"] <- as.factor(rep(sex, nrow(newdd)))
newdd["RecDate"] <- (rep(rec_date, nrow(newdd)))
newdd["Code"] <- rep(code, nrow(newdd))
newdd["ID"] <- as.factor(rep(id, nrow(newdd)))
newdd["AgeDays"] <- rep(age_d, nrow(newdd))
newdd["AgeYears"] <- rep(age_y, nrow(newdd))
newdd["SourceFile"] <- rep(source_fyle, nrow(newdd))
newdd["CallFile"] <- call_fyle
newdd["CallType"] <- call_type
newdd["CallTime"] <- annot_dd["Start"]

meta_dd <- rbind(meta_dd, newdd)
write.csv(meta_dd, "audio_metadata.csv", row.names = FALSE)

rm(list = ls())