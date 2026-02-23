import os
import shutil
import json


json_file = "/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/cleanresult.json"
source_folder = "/home/paulkim/Documents/nest_seven"
destination_folder = "/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/images"


with open(json_file, "r") as f:
   data = json.load(f)


image_filenames = set()
for image in data.get("images", []):
   file_path = image.get("file_name", "")
   filename = os.path.basename(file_path)
   image_filenames.add(filename)


for filename in os.listdir(source_folder):
   if filename in image_filenames:
       source_path = os.path.join(source_folder, filename)
       destination_path = os.path.join(destination_folder, filename)
       shutil.move(source_path, destination_path)
       print(f"Moved: {filename}")