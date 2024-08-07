import traceback

from editor.editor import Editor
from parameters import InputParameter
import argparse
import os


def execute(*args, input_file, **kwargs):
    try:
        with InputParameter(*args, input_file=input_file, **kwargs) as parameter:
            editor = Editor(parameter)
            editor.execute()
    except Exception as e:
        print(f"Error process file {input_file} with exception: {e}")
        traceback.print_exc()


def main(*args, input_file=None, output_file=None, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str)
    parser.add_argument('--output_file', type=str)
    parsed_args, _ = parser.parse_known_args()
    input_dir: str = input_file or parsed_args.input_file
    output_dir: str = output_file or parsed_args.output_file

    if input_dir and os.path.isdir(input_dir):
        input_file_names = filter(lambda f: os.path.isfile(f), os.listdir(input_dir))
        input_files = list(map(lambda f: os.path.join(input_dir, f), input_file_names))

        if output_dir and os.path.isdir(output_dir):
            output_files = map(lambda f: os.path.join(output_dir, f), input_file_names)
        else:
            output_files = [None] * len(input_files)

        for input_file, output_file in zip(input_files, output_files):
            execute(args, input_file=input_file, output_file=output_file, **kwargs)

    else:
        execute(args, input_file=input_file, output_file=output_file, **kwargs)


if __name__ == '__main__':
    main()
