from functools import reduce
import re

from timecode import Timecode

from editor.edit_point import EditPoint
from utils.timecode_utils import format_timecode


class Section:

    def __init__(self, start_frame, title):
        self.start_frame = start_frame
        self.end_frame = -1
        self.title = title

        self.edit_offset = 0

    def apply_edit_point(self, edit_point: EditPoint):
        if edit_point.end_frame < self.start_frame:
            self.edit_offset -= edit_point.end_frame - edit_point.start_frame
        elif edit_point.start_frame < self.start_frame:
            self.edit_offset -= self.start_frame - edit_point.start_frame

    @property
    def frame_count(self):
        return self.end_frame - self.start_frame

    @staticmethod
    def parse(text: str, frame_rate):
        def parse_section(section_text: str):
            start_time, title = re.split(r"\s+", section_text, maxsplit=1)
            start_frame = Timecode(frame_rate, start_timecode=format_timecode(start_time)).frames
            return Section(start_frame, title)

        return list(map(parse_section, text.splitlines(keepends=False)))

    @staticmethod
    def compute_frames(sections: list['Section'], total_frame_count: int):
        if not sections:
            return
        sections.sort(key=lambda s: s.start_frame)

        def apply_end_frame(p, n):
            p.end_frame = n.start_frame
            return n

        def consume_edit(section: 'Section') -> 'Section':
            section.start_frame += section.edit_offset
            section.edit_offset = 0
            return section

        reduce(apply_end_frame, map(lambda s: consume_edit(s), sections))
        # include the last frame.
        sections[-1].end_frame = total_frame_count + 1
