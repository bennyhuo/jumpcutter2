import math
import sys

import numpy as np
from audiotsm import phasevocoder
from audiotsm.io.array import ArrayReader, ArrayWriter

from editor.edit_point import EditPoint
from editor.outputs import EdlOutput, DirectVideoOutput
from parameters import InputParameter, get_max_volume


class Editor:

    def __init__(self, parameter: InputParameter):
        self.parameter = parameter
        self.last_progress = 0

    def get_loud_frame(self):
        has_loud_audio = np.zeros(self.parameter.audio_frame_count)

        # keep start
        for i in range(0, self.parameter.keep_frames_from_start):
            has_loud_audio[i] = 1

        # check content
        frames_count_to_cut = self.parameter.audio_frame_count - self.parameter.keep_frames_from_end
        for i in range(self.parameter.keep_frames_from_start, frames_count_to_cut):
            start = int(i * self.parameter.samples_per_frame)
            end = min(int((i + 1) * self.parameter.samples_per_frame), self.parameter.audio_sample_count)
            audio_chunks = self.parameter.audio_data[start:end]
            max_chunks_volume = float(get_max_volume(audio_chunks)) / self.parameter.max_audio_volume
            if max_chunks_volume >= self.parameter.silent_threshold:
                has_loud_audio[i] = 1

        # keep end
        for i in range(frames_count_to_cut, self.parameter.audio_frame_count):
            has_loud_audio[i] = 1

        return has_loud_audio

    def get_edit_points(self, has_loud_audio):
        edit_points = [EditPoint(0, 0, 0)]
        should_include_frame = np.zeros(self.parameter.audio_frame_count)
        for i in range(self.parameter.audio_frame_count):
            start = int(max(0, i - self.parameter.frame_margin))
            end = int(min(self.parameter.audio_frame_count, i + 1 + self.parameter.frame_margin))
            should_include_frame[i] = np.max(has_loud_audio[start:end])
            if i >= 1 and should_include_frame[i] != should_include_frame[i - 1]:  # Did we flip?
                edit_points.append(EditPoint(edit_points[-1].end_frame, i, should_include_frame[i - 1]))

        edit_points.append(EditPoint(edit_points[-1].end_frame, self.parameter.audio_frame_count,
                                     should_include_frame[self.parameter.audio_frame_count - 1]))
        return edit_points[1:]

    def get_output(self):
        return EdlOutput(parameter=self.parameter) \
            if self.parameter.output_type == 'edl' else DirectVideoOutput(parameter=self.parameter)

    def fade_out_silence(self, audio_data):
        fade_mask = np.arange(self.parameter.audio_fade_envelope_size) / self.parameter.audio_fade_envelope_size
        mask = np.repeat(fade_mask[:, np.newaxis], 2, axis=1)  # make the fade-envelope mask stereo
        audio_data[:self.parameter.audio_fade_envelope_size] *= mask
        audio_data[- self.parameter.audio_fade_envelope_size:] *= 1 - mask

    def execute(self):
        # get values of audio frames, 0 for silence, 1 for loudness.
        has_loud_audio = self.get_loud_frame()
        # get edit points of silence and loudness.
        edit_points = self.get_edit_points(has_loud_audio)

        start_frame = 0
        output = self.get_output()
        for edit_point in edit_points:
            audio_chunk = self.parameter.audio_data[
                          int(edit_point.start_frame * self.parameter.samples_per_frame):
                          int(edit_point.end_frame * self.parameter.samples_per_frame)
                          ]

            # need channels * frames, transpose data first.
            reader = ArrayReader(np.transpose(audio_chunk))
            writer = ArrayWriter(reader.channels)
            tsm = phasevocoder(reader.channels, speed=self.parameter.new_speed[int(edit_point.should_keep)])
            tsm.run(reader, writer)
            altered_audio_data = np.transpose(writer.data)

            altered_audio_data_length = altered_audio_data.shape[0]
            if altered_audio_data_length < self.parameter.audio_fade_envelope_size:
                altered_audio_data[:] = 0  # audio is less than 0.01 sec, let's just remove it.
            else:
                self.fade_out_silence(altered_audio_data)
            end_frame = start_frame + altered_audio_data_length

            start_output_frame = int(math.ceil(start_frame / self.parameter.samples_per_frame))
            end_output_frame = int(math.ceil(end_frame / self.parameter.samples_per_frame))

            output.apply_edit_point(edit_point, altered_audio_data, start_output_frame, end_output_frame)
            self.print_progress(edit_point.end_frame, self.parameter.audio_frame_count)

            start_frame = end_frame

        output.close()

    def print_progress(self, current, total):
        progress = current * 100 / total
        if progress - self.last_progress > 1:
            self.last_progress = progress
            sys.stdout.write(f"\rAnalyzing [{('=' * int(progress / 5)):20s}] {progress:.1f}%({current}/{total})")
            sys.stdout.flush()
        elif current == total:
            self.last_progress = progress
            sys.stdout.write(f"\rAnalyzing [{('=' * int(progress / 5)):20s}] {progress:.1f}%({current}/{total})\n")
            sys.stdout.flush()


