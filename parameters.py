import argparse
import math
import re
import sys

import numpy as np
from scipy.io import wavfile

import io_utils
from shell_utils import do_shell, STRING


def get_max_volume(s):
    max_value = float(np.max(s))
    min_value = float(np.min(s))
    return max(max_value, -min_value)


class InputParameter:

    def __init__(self, *args, input_file=None,
                 url=None,
                 output_type=None,
                 output_file=None,
                 silent_threshold=None,
                 sounded_speed=None,
                 silent_speed=None,
                 frame_margin=None,
                 sample_rate=None,
                 frame_rate=None,
                 frame_quality=None,
                 temp_folder=None):

        parser = argparse.ArgumentParser(
            description='Modifies a video file to play at different speeds '
                        'when there is sound vs. silence.')
        parser.add_argument('--input_file', type=str, help='the video file you want modified')
        parser.add_argument('--output_type', type=str, default="video", help='output type: video, edl')
        parser.add_argument('--url', type=str, help='A youtube url to download and process')
        parser.add_argument('--output_file', type=str, default="",
                            help="the output file. "
                                 "(optional. if not included, it'll just modify the input file name)")
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
        parser.add_argument('--frame_quality', type=int, default=3,
                            help="quality of frames to be extracted from input video. "
                                 "1 is highest, 31 is lowest, 3 is the default.")
        parser.add_argument('--temp_folder', type=str, default=".temp",
                            help="temp folder for intermediates process.")

        args = parser.parse_args()

        self.temp_folder = temp_folder or args.temp_folder

        self.frame_rate = frame_rate or args.frame_rate
        self.sample_rate = sample_rate or args.sample_rate
        self.silent_threshold = silent_threshold or args.silent_threshold
        self.frame_margin = frame_margin or args.frame_margin
        self.new_speed = [silent_speed or args.silent_speed, sounded_speed or args.sounded_speed]
        url = url or args.url
        if url:
            self.input_file = io_utils.download_file(args.url)
        else:
            self.input_file = input_file or args.input_file

        # input_file is required
        if not self.input_file:
            parser.print_help()
            sys.exit(-1)

        self.frame_quality = frame_quality or args.frame_quality

        self.output_type = output_type or args.output_type
        self.output_file = output_file or args.output_file
        self.frame_rate = frame_rate or args.frame_rate

        self.audio_fade_envelope_size = 400

    def __enter__(self):
        io_utils.create_path(self.temp_folder)

        do_shell(f'ffmpeg -i "{self.input_file}" -ab 160k -ac 2 -ar '
                 f'{str(self.sample_rate)} -vn {self.temp_folder}/audio.wav')

        self.audio_sample_rate, self.audio_data = wavfile.read(f"{self.temp_folder}/audio.wav")
        self.audio_sample_count = self.audio_data.shape[0]
        self.max_audio_volume = get_max_volume(self.audio_data)

        # try to detect frame rate
        video_parameters = do_shell(f'ffmpeg -i "{self.input_file}"', STRING, 'utf-8').split('\n')
        auto_detected_frame_rate = None
        for line in video_parameters:
            m = re.search('Stream #.*Video.* ([0-9]*) fps', line)
            if m is not None:
                auto_detected_frame_rate = float(m.group(1))

        self.frame_rate = auto_detected_frame_rate or self.frame_rate
        self.samples_per_frame = self.audio_sample_rate / self.frame_rate

        self.audio_frame_count = int(math.ceil(self.audio_sample_count / self.samples_per_frame))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        io_utils.delete_path(self.temp_folder)
