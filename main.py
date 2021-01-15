import os
import jumpcutter

files = os.listdir("build/data")
print(files)
for file in files:
    if not os.path.exists(f"build/trimmed/{file}"):
        # os.system(f'jumpcutter.py --input_file "data/{file}" --output_file "trimmed/{file}" --silent_speed 9999 --frame_margin 3')
        jumpcutter.main(input_file=f"build/data/{file}", output_type="edl", output_file=f"build/trimmed/{file}.edl", silent_speed=2, frame_margin=3)
        # jumpcutter.main(input_file=f"data/{file}", output_type="edl", output_file=f"trimmed/{file}_cut.edl", silent_speed=9999, frame_margin=3)
        # jumpcutter.main(input_file=f"data/{file}", output_file=f"trimmed/{file}", silent_speed=2, frame_margin=3)
