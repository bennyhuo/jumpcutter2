import os
import jumpcutter
from shell_utils import do_shell, STRING, take_until

result = do_shell(f'ffmpeg -encoders', stdout=STRING)

print(result)

h264_encoders = [encoder[1] for encoder in [
    line.strip().split(' ', 2)[:2] for line in take_until(result.splitlines(), lambda line: line.strip() == '------')
] if encoder[0] == 'V....D' and encoder[1].startswith('h264')]

print(h264_encoders)

# jumpcutter.main(input_file=f"build/data", output_type="video", silent_speed=9999, frame_margin=3)
# jumpcutter.main(input_file=f"build/data", output_file="build/trimmed", output_type="video", silent_speed=9999, frame_margin=3)

#
# files = os.listdir("build/data")
# print(files)
# for file in files:
#     if not os.path.exists(f"build/trimmed/{file}"):
#         # os.system(f'jumpcutter.py --input_file "data/{file}" --output_file "trimmed/{file}" --silent_speed 9999 --frame_margin 3')
#         # jumpcutter.main(input_file=f"build/data/{file}", output_type="edl", output_file=f"build/trimmed/{file}.edl", silent_speed=2, frame_margin=3)
#         jumpcutter.main(input_file=f"build/data/{file}", output_type="video", silent_speed=9999, frame_margin=3)
#         # jumpcutter.main(input_file=f"data/{file}", output_type="edl", output_file=f"trimmed/{file}_cut.edl", silent_speed=9999, frame_margin=3)
#         # jumpcutter.main(input_file=f"data/{file}", output_file=f"trimmed/{file}", silent_speed=2, frame_margin=3)
