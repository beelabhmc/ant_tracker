def main():
    success = True
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    try:
        import cv2
    except ImportError:
        missing.append('opencv')
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')
    try:
        import matlab.engine
    except ImportError:
        missing.append('the Matlab Python Engine')
    try:
        from subprocess import run
        ffmpeg = (run('ffmpeg', shell=True, capture_output=True).returncode != 127)
        if not ffmpeg:
            missing.append('ffmpeg')
    except Exception:
        missing.append('ffmpeg')
    if missing:
        sucess = False
        for package in missing:
            print('You do not have {}.'.format(package))
    import sys
    if sys.version_info < (3, 6, 0):
        print('You need to use python >=3.6, not {}.'.format(sys.version))
        success = False
    if success:
        print('You\'re good to go!')
        exit(0)
    exit(1)

if __name__ == '__main__':
    main()

