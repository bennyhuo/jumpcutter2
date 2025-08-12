import argparse
import datetime
import json
import math
import os.path
import re
import tempfile

import numpy as np
from scipy.io import wavfile
from timecode import Timecode

from utils import io_utils
from utils.shell_utils import do_shell, STRING


def get_max_volume(s):
    max_value = float(np.max(s))
    min_value = float(np.min(s))
    return max(max_value, -min_value)


class InputParameter:

    def __init__(self, *args,
                 input_file=None,
                 input_sections=None,
                 url=None,
                 output_type=None,
                 output_file=None,
                 mapping=None,
                 silent_threshold=None,
                 sounded_speed=None,
                 silent_speed=None,
                 frame_margin=None,
                 sample_rate=None,
                 frame_rate=None,
                 bit_rate=None,
                 frame_quality=None,
                 temp_folder=None,
                 keep_start=None,
                 keep_end=None,
                 use_hardware_acc=None):

        parser = argparse.ArgumentParser(
            description='Modifies a video file to play at different speeds '
                        'when there is sound vs. silence.')
        parser.add_argument('--input_file', type=str, help='the video file you want modified')
        parser.add_argument(
            '--input_sections', type=str,
            help='The file contains video sections information. '
                 'Each section contains a start time and a title like "00:12 section 1" separated by new lines.'
        )
        parser.add_argument('--output_type', type=str, default="video", help='output type: video, edl')
        parser.add_argument('--url', type=str, help='A youtube url to download and process')
        parser.add_argument('--output_file', type=str, default="",
                            help="the output file. "
                                 "(optional. if not included, it'll just modify the input file name)")
        parser.add_argument('--mapping', type=str, default="",
                            help="Time mapping should be applied to the input file."
                                 "(optional)")
        parser.add_argument('--silent_threshold', type=float, default=0.03,
                            help='the volume amount that frames\' audio needs to surpass to be consider "sounded". '
                                 'It ranges from 0 (silence) to 1 (max volume)')
        parser.add_argument('--sounded_speed', type=float, default=1.00,
                            help="the speed that sounded (spoken) frames should be played at. Typically 1.")
        parser.add_argument('--silent_speed', type=float, default=5.00,
                            help="the speed that silent frames should be played at. 999999 for jumpcutting.")
        parser.add_argument('--frame_margin', type=float, default=1,
                            help="some silent frames adjacent to sounded frames are included to provide context. "
                                 "How many frames on either the side of speech should be included? "
                                 "That's this variable.")
        parser.add_argument('--sample_rate', type=float, default=44100,
                            help="sample rate of the input and output videos")
        parser.add_argument('--frame_rate', type=float, default=30,
                            help="frame rate of the input and output videos. optional.")
        parser.add_argument('--bit_rate', type=float, default=1000,
                            help="bit rate of the input and output videos. optional. Default 1000kbps")
        parser.add_argument('--frame_quality', type=int, default=3,
                            help="quality of frames to be extracted from input video. "
                                 "1 is highest, 31 is lowest, 3 is the default.")
        parser.add_argument('--temp_folder', type=str,
                            help="temp folder for intermediates process.")

        parser.add_argument('--keep_start', type=int, default=0,
                            help="Seconds for not cutting from start.")
        parser.add_argument('--keep_end', type=int, default=0,
                            help="Seconds for not cutting from end.")
        parser.add_argument('--use_hardware_acc', type=int, default=0,
                            help="[Experimental] Enable hardware acceleration when encoding.")

        args = parser.parse_args()

        self.temp_folder = temp_folder or args.temp_folder or tempfile.mkdtemp('jumpcut_')

        self.frame_rate = frame_rate or args.frame_rate
        self.sample_rate = sample_rate or args.sample_rate
        self.bit_rate = bit_rate or args.bit_rate
        self.silent_threshold = silent_threshold or args.silent_threshold
        self.frame_margin = frame_margin or args.frame_margin
        self.new_speed = [silent_speed or args.silent_speed, sounded_speed or args.sounded_speed]
        url = url or args.url
        if url:
            self.input_file = io_utils.download_file(args.url)
        else:
            self.input_file = input_file or args.input_file
        self.input_sections = input_sections or args.input_sections

        # input_file is required
        if not self.input_file:
            parser.print_help()
            raise Exception("input_file is required.")

        self.frame_quality = frame_quality or args.frame_quality

        self.output_type = output_type or args.output_type
        self.output_file = output_file or args.output_file
        self.replace = self.output_type != 'edl' and not self.output_file
        if self.replace:
            print("The input file will be replaced with the output file.")
        self.mapping = mapping or args.mapping

        self.frame_rate = frame_rate or args.frame_rate

        self.keep_frames_from_start = self.frame_rate * (keep_start or args.keep_start)
        self.keep_frames_from_end = self.frame_rate * (keep_end or args.keep_end)

        self.audio_fade_envelope_size = 400
        self.use_hardware_acc = use_hardware_acc or args.use_hardware_acc

    def __enter__(self):
        io_utils.create_path(self.temp_folder)

        do_shell(f'ffmpeg -hide_banner -i "{self.input_file}" -ab 160k -ac 2 -ar '
                 f'{str(self.sample_rate)} -vn "{self.temp_folder}/audio.wav"')

        self.audio_sample_rate, self.audio_data = wavfile.read(f"{self.temp_folder}/audio.wav")
        self.audio_sample_count = self.audio_data.shape[0]
        self.max_audio_volume = get_max_volume(self.audio_data)

        # try to detect frame rate
        video_parameters = do_shell(f'ffmpeg -i "{self.input_file}"', STRING, 'utf-8').split('\n')
        auto_detected_frame_rate = None
        auto_detected_bit_rate = None

        self.video_width = None
        self.video_height = None
        for line in video_parameters:
            match = re.search(r'Duration: ((\d{2}):(\d{2}):(\d{2})[;:.](\d+)), ', line)
            if match:
                self.duration = match.group(1)
            else:
                # Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661),
                # yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 131 kb/s, 30 fps, 30 tbr,
                # 30k tbn (default)
                match = re.search(r'Stream #.*Video.*, (\d+)x(\d+).* (\d+) kb/s.*?(\d+) fps', line)
                if match is not None:
                    self.video_width = int(match.group(1))
                    self.video_height = int(match.group(2))
                    auto_detected_bit_rate = float(match.group(3))
                    auto_detected_frame_rate = float(match.group(4))

        if not self.video_width:
            self.audio_only = True
            self.input_sections = None
        else:
            self.audio_only = False
            self.detect_sections()


        self.bit_rate = auto_detected_bit_rate or self.bit_rate
        self.frame_rate = auto_detected_frame_rate or self.frame_rate
        self.samples_per_frame = self.audio_sample_rate / self.frame_rate

        self.audio_frame_count = int(math.ceil(self.audio_sample_count / self.samples_per_frame))

        if self.duration:
            tc = Timecode(self.frame_rate, start_timecode=self.duration)
            self.duration = tc.secs
            self.video_frame_count = tc.frames
        else:
            raise RuntimeError("Video duration parse error.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        io_utils.delete_path(self.temp_folder)

    def detect_sections(self):
        if self.input_sections:
            return

        detected_section_file = f"{self.input_file.rsplit('.', 1)[0]}.sec"
        if os.path.exists(detected_section_file):
            self.input_sections = detected_section_file
            print(f"Auto detected sections file: {detected_section_file}")
            return

        # detect sections from video
        raw_chapters = do_shell(f'ffprobe -i {self.input_file} -print_format json -show_chapters -loglevel fatal',
                                STRING)
        parsed_chapters = json.loads(raw_chapters)
        print(parsed_chapters)

        if 'chapters' in parsed_chapters:
            chapters = parsed_chapters['chapters']
            if chapters:
                with open(detected_section_file, 'w') as file:
                    for chapter in chapters:
                        start_time_secs = int(float(chapter['start_time']))
                        start_time = f'{start_time_secs // 60}:{start_time_secs % 60}'
                        end_time_secs = int(float(chapter['end_time']))
                        end_time = f'{end_time_secs // 60}:{end_time_secs % 60}'
                        title = chapter['tags']['title']
                        file.write(f'{start_time} {end_time} {title}\n')
                self.input_sections = detected_section_file
