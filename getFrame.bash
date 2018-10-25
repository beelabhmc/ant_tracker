#!/bin/bash

# inputs:
#	path to video file from which to get frame,
#	position of frame in the video
#		ie number of seconds (as int or decimal) or a time format (like 4:57),
#	path to output directory
# ex1: ./getFrame.bash storage/C1O-seg10.mp4 7 out/frame/
# ex2: ./getFrame.bash storage/C1O-seg10.mp4 5:03 out/frame/

# make output directory if it doesn't exist
mkdir -p "$3"
# get video filename
fname="${1##*/}"
# execute ffmpeg
# when creating output path,
#	remove any trailing slashes from specificed output directory
#	and remove video extension
# note that we use the -y option to overwrite files if they exist already
# also use the loglevel option to disable any ffmpeg output that isn't an error/warning
ffmpeg -y -loglevel warning -i "$1" -ss "$2" -vframes 1 "${3%/}/${fname%.*}".png