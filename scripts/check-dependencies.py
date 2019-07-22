def main():
    """Check that all the necessary imports are here."""
    success = True
    missing = []
    try:
        import snakemake
    except ImportError:
        missing.append('snakemake')
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    try:
        import cv2
        if cv2.__version__[0] != '4':
            print('You need OpenCV version 4.x, not %s' % cv2.__version__)
            success = False
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
        code = run('ffmpeg', shell=True, capture_output=True).returncode
        if code == 127:
            missing.append('ffmpeg')
    except Exception:
        missing.append('ffmpeg')
    if missing:
        sucess = False
        for package in missing:
            print('You do not have %s.' % package)
    import sys
    if sys.version_info < (3, 6, 0):
        print('You need to use python >=3.6, not %s.' % sys.version)
        success = False
    if success:
        print('You\'re good to go!')
        exit(0)
    exit(1)

if __name__ == '__main__':
    main()

