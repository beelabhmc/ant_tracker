import sys
from moviepy.editor import VideoFileClip

def preprocess_video(input_path, output_path):
    # Check if the input video has the .mov extension
    video = VideoFileClip(input_path)

    # Trim the first and last 5 seconds of the video
    trimmed_video = video.subclip(5, video.duration - 5)

    # Write the processed video to the output path
    trimmed_video.write_videofile(output_path)

def main():
    print('''
    |\---/|
    | o_o |
     \_^_/
     ''')
    # Check if the correct number of command line arguments is provided
    if len(sys.argv) != 3:
        print("Whoopsies")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    print("input:", input_path, "output:", output_path)
    # Perform video preprocessing
    preprocess_video(input_path, output_path)

if __name__ == '__main__':
    main()