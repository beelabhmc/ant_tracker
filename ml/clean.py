import json
import re


input_file = "/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/result.json"
output_file = "/home/paulkim/Documents/BeeLabSM2025/ml-ant_tracker/ant_tracker/ml/export_176945_project-176945-at-2025-07-30-22-46-72354786/cleanresult.json"

with open(input_file, "r") as f:
    data = json.load(f)


for image in data.get("images", []):
    original = image.get("file_name", "")
    match = re.search(r"(frame.*)", original)
    if match:
        image["file_name"] = match.group(1)
    
    # GoPro Camera Specs
    image["width"] = 3840
    image["height"] = 2160


for ann in data.get("annotations", []):
    # For pytorch the background has to be zero
    if ann.get("category_id") == 0:
        ann["category_id"] = 1



for cat in data.get("categories", []):
    if cat.get("id") == 0:
        cat["id"] = 1


with open(output_file, "w") as f:
    json.dump(data, f, indent=2)


print(f"Cleaned file names and fixed category IDs saved to '{output_file}'.")