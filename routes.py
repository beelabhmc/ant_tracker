def routes(vid, tracks, output):
	"""
		plot the routes of individual ants on top of an image of their bridge
		inputs:
			vid - the path to the video of their bridge
			tracks - a np array containing ant tracks
				with cols: x_pos, y_pos, width, height, ant_id
			output - the path to the output dir
	"""