def format_timecode(timecode_str: str):
    delimiters = iter([";", "."])
    for delimiter in delimiters:
        parts = timecode_str.split(delimiter)
        if len(parts) > 2:
            raise RuntimeError("Illegal timecode.")
        if len(parts) == 2:
            break
    else:
        parts = [timecode_str, '00']

    parts = [*parts[0].split(":"), parts[1]]
    while len(parts) < 4:
        parts.insert(0, '00')

    return ":".join(parts)


if __name__ == '__main__':
    print(format_timecode("00.12"))
    print(format_timecode("12"))
    print(format_timecode("00:00.12"))
    print(format_timecode("00:01:20;12"))
