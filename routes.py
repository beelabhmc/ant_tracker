import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as colors
import matplotlib.cm as cm
from PIL import Image
import numpy as np
from itertools import tee, izip
import random

def pairwise(iterable):
    """
    	returns an iterator that can traverse over an iterable by pairs
    	https://docs.python.org/3/library/itertools.html?highlight=pairwise
    	ex: s -> (s0,s1), (s1,s2), (s2, s3), ...
    """
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def unique_colors(vmin, vmax):
	"""
		create a generator for unique matplotlib colors
	"""
	color_convert = cm.ScalarMappable(norm=colors.Normalize(vmin=vmin, vmax=vmax), cmap=cm.hot)
	seen = set({})
	while True:
		color = color_convert.to_rgba(random.uniform(0, 1))
		if color in seen:
			continue
		seen.add(color)
		yield color

def routes(vid, tracks, output):
	"""
		plot the routes of individual ants on top of an image of their bridge
		inputs:
			vid - the path to the video of their bridge
			tracks - a np array containing ant tracks
				with cols: x_pos, y_pos, width, height, ant_id
			output - the path to the output dir
	"""
	# import image as np array and add it to an AxesImage
	im = np.array(Image.open(vid), dtype=np.uint8)
	fig, ax = plt.subplots(1)
	ax.imshow(im)
	colors = unique_colors(-100, 100)
	# add arrows for each ant
	for ant in np.unique(tracks[:, 4]):
		# get tracks for this ant
		ant_tracks = tracks[tracks[:, 4] == ant]
		# get a unique color for this ant
		color = next(colors)
		# iterate over each pair of rows in the dataframe
		for track_pair in pairwise(ant_tracks):
			# get origin and destination points
			origin = track_pair[0]
			dest = track_pair[1]
			# create arrow from origin to destination
			# note that destination must be provided as a delta value
			arrow = patches.Arrow(
				origin[0], origin[1],
				dest[0]-origin[0], dest[1]-origin[1],
				width = 1, edgecolor = color
			)
			# add arrow to AxesImage
			ax.add_patch(arrow)
	plt.show()