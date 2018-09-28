#!/bin/bash
ffmpeg -i "$1" -ss 00:00:07.000 -vframes 1 thumb.jpg