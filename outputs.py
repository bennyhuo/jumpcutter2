import locale
import os
from shutil import copyfile

import numpy as np
from scipy.io import wavfile
from timecode import Timecode

from edit_point import EditPoint
from parameters import InputParameter
from shell_utils import do_shell, STRING, take_until

OS_ENCODING = locale.getpreferredencoding()


class BaseOutput(object):

    def __init__(self, parameter: InputParameter):
        self.parameter = parameter

        self.input_file_dir = os.path.dirname(parameter.input_file)
        self.input_file_name = os.path.basename(parameter.input_file)
        self.input_file_name_without_extension = self.input_file_name[:self.input_file_name.rfind('.')]

    def apply_edit_point(self, edit_point: EditPoint, audio_data, start_output_frame, end_output_frame):
        pass

    def close(self):
        pass


class EdlOutput(BaseOutput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.parameter.output_file:
            self.parameter.output_file = os.path.join(
                self.input_file_dir,
                f'{self.input_file_name_without_extension}.edl'
            )

        self.edl_file = open(self.parameter.output_file, "w", encoding=OS_ENCODING)
        self.edl_file.write(f'TITLE: {self.input_file_name_without_extension}\n\n')

        self.index = 1

    def apply_edit_point(self, edit_point: EditPoint, audio_data, start_output_frame, end_output_frame):
        edit_point_output_start = Timecode(self.parameter.frame_rate, frames=start_output_frame + 1)
        edit_point_output_end = Timecode(self.parameter.frame_rate, frames=end_output_frame + 1)
        # provide one frame buffer for motion events. if the output length is less than 2 frames, cut it off.
        if edit_point_output_end.frames - edit_point_output_start.frames > 1:
            edit_point_start = Timecode(self.parameter.frame_rate, frames=edit_point.start_frame + 1)
            edit_point_end = Timecode(self.parameter.frame_rate, frames=edit_point.end_frame + 1)

            self.edl_file.write(
                f'{self.index:03d}  AX       AA/V  C        '
                f'{edit_point_start} {edit_point_end} {edit_point_output_start} {edit_point_output_end}\n')
            self.edl_file.write(f'* FROM CLIP NAME: {self.input_file_name}\n')

            if not edit_point.should_keep:
                # M2   AX       086.7                      00:00:16:16
                output_length = edit_point_output_end - edit_point_output_start
                original_length = edit_point_end - edit_point_start
                if output_length != original_length:
                    # adobe premiere may complain about the motion events with such an 'accurate' new_frame_rate.
                    # so we leave one frame as a buffer to hold the whole input video frames after speed changes.
                    # it's safe to subtract 1 from output_length as we have already guaranteed 2 frames at least.
                    new_frame_rate = original_length.frames / (output_length.frames - 1) * self.parameter.frame_rate
                    self.edl_file.write(
                        f'M2   AX       '
                        f'{new_frame_rate:05.1f}'
                        f'                      '
                        f'{edit_point_start}\n'
                    )

            self.edl_file.write('\n')
            self.index += 1

    def close(self):
        self.edl_file.close()


class DirectVideoOutput(BaseOutput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.parameter.output_file:
            self.parameter.output_file = os.path.join(
                self.input_file_dir,
                f'{self.input_file_name_without_extension}_edited{self.input_file_name[self.input_file_name.rfind("."):]}'
            )

        self.audio_edit_config = []
        self.video_edit_config = []

    def apply_edit_point(self, edit_point: EditPoint, audio_data, start_output_frame, end_output_frame):
        edit_point_output_start = Timecode(self.parameter.frame_rate, frames=start_output_frame + 1)
        edit_point_output_end = Timecode(self.parameter.frame_rate, frames=end_output_frame + 1)

        # provide one frame buffer for motion events. if the output length is less than 2 frames, cut it off.
        if edit_point_output_end.frames - edit_point_output_start.frames <= 1:
            edit_point_start = Timecode(self.parameter.frame_rate, frames=edit_point.start_frame + 1)
            edit_point_end = Timecode(self.parameter.frame_rate, frames=edit_point.end_frame + 1)
            self.video_edit_config.append(f"between(n, {edit_point_start.frames}, {edit_point_end.frames - 1})")
            self.audio_edit_config.append(f"between(t, {edit_point_start.float}, {edit_point_end.float})")

    def select_encoder(self):
        if self.parameter.use_hardware_acc:
            result = do_shell(f'ffmpeg -encoders', stdout=STRING)
            h264_encoders = [encoder[1] for encoder in [
                line.strip().split(' ', 2)[:2] for line in
                take_until(result.splitlines(), lambda line: line.strip() == '------')
            ] if encoder[0] == 'V....D' and encoder[1].startswith('h264')]

            print(f'hardware h264 encoders: {h264_encoders}')

            if not h264_encoders:
                return ''

            preferred_encoders = ['h264_nvenc', 'h264_videotoolbox']
            selected_encoder = None
            for preferred_encoder in preferred_encoders:
                if preferred_encoder in h264_encoders:
                    selected_encoder = preferred_encoder
                    break
            else:
                selected_encoder = h264_encoders[0]

            print(f'selected encoder: {selected_encoder}')
            return f'-c:v {selected_encoder}'

    def close(self):
        with open(f"{self.parameter.temp_folder}/filter_script.txt", "w", encoding=OS_ENCODING) as config_file:
            config_file.write("select='not(\n")
            config_file.write("+".join(self.video_edit_config))
            config_file.write(")',setpts=N/FR/TB; \n")

            config_file.write("aselect='not(\n")
            config_file.write("+".join(self.audio_edit_config))
            config_file.write(")', asetpts=N/SR/TB\n")

        # Use ffmpeg filter to cut videos directly if possible.
        hw_encoder = self.select_encoder()

        do_shell(
            f'ffmpeg -thread_queue_size 1024 '
            f'-y -filter_complex_script "{self.parameter.temp_folder}/filter_script.txt" '
            f'-i "{self.parameter.input_file}" {hw_encoder} -b:v {self.parameter.bit_rate}k "{self.parameter.output_file}"'
        )

        if self.parameter.replace:
            from send2trash import send2trash

            send2trash(self.parameter.input_file)
            os.rename(self.parameter.output_file, self.parameter.input_file)
            print(f"Output file: {self.parameter.output_file}")



# Deprecated. Will be removed soon.
class LegacyVideoOutput(BaseOutput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.parameter.output_file:
            self.parameter.output_file = os.path.join(
                self.input_file_dir,
                f'{self.input_file_name_without_extension}_edited{self.input_file_name[self.input_file_name.rfind("."):]}'
            )

        do_shell(
            f'ffmpeg -i "{self.parameter.input_file}" -qscale:v {str(self.parameter.frame_quality)} "{self.parameter.temp_folder}/frame%06d.jpg" -hide_banner')

        self.last_existing_frame = None
        self.output_audio_data = np.zeros((0, self.parameter.audio_data.shape[1]))

    def apply_edit_point(self, edit_point: EditPoint, audio_data, start_output_frame, end_output_frame):
        self.output_audio_data = np.concatenate(
            (self.output_audio_data, audio_data / self.parameter.max_audio_volume))

        for outputFrame in range(start_output_frame, end_output_frame):
            input_frame = int(
                edit_point.start_frame + self.parameter.new_speed[int(edit_point.should_keep)] * (
                            outputFrame - start_output_frame))
            did_it_work = self.copy_frame(input_frame, outputFrame)
            if did_it_work:
                self.last_existing_frame = input_frame
            else:
                self.copy_frame(self.last_existing_frame, outputFrame)

    def copy_frame(self, input_frame, output_frame):
        src = f"{self.parameter.temp_folder}/frame{input_frame + 1:06d}.jpg"
        dst = f"{self.parameter.temp_folder}/newFrame{output_frame + 1:06d}.jpg"
        if not os.path.isfile(src):
            return False
        copyfile(src, dst)
        if output_frame % 20 == 19:
            print(str(output_frame + 1) + " time-altered frames saved.")
        return True

    def close(self):
        wavfile.write(f'{self.parameter.temp_folder}/audioNew.wav', self.parameter.sample_rate, self.output_audio_data)

        do_shell(
            f'ffmpeg -thread_queue_size 1024 -framerate {str(self.parameter.frame_rate)} '
            f'-i "{self.parameter.temp_folder}/newFrame%06d.jpg" -i "{self.parameter.temp_folder}/audioNew.wav" -strict -2 "{self.parameter.output_file}"'
        )
