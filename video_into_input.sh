#!/bin/zsh

if [ $# -ne 2 ]; then
    echo "Usage: $0 <year_video_recorded> <team_name>"
    exit 1
fi

year_video_recorded="$1"
team_name="$2"

find "/mnt/biology/donaldson/ant_videos/$year_video_recorded" \( -iname "*.mp4" -o -iname "*.MP4" -o -iname "*.mov" -o -iname "*.MOV" \) -exec zsh -c '
    for file do
        target=$(basename "$file")
        ln -s "$file" "/mnt/biology/donaldson/'"$team_name"'/ant_tracker/input/$target"
        extension="${target##*.}"
        lowercase_extension=$(echo "$extension" | tr "[:upper:]" "[:lower:]")
        if [ "$extension" != "$lowercase_extension" ]; then
            mv "/mnt/biology/donaldson/'"$team_name"'/ant_tracker/input/$target" "/mnt/biology/donaldson/'"$team_name"'/ant_tracker/input/${target%.*}.$lowercase_extension"
        fi
    done
' zsh {} +
