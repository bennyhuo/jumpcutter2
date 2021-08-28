from editor import Editor
from parameters import InputParameter
import argparse
import os


def main(*args, input_file=None, output_file=None, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str)
    parser.add_argument('--output_file', type=str)
    parsed_args = parser.parse_args()
    input_dir: str = input_file or parsed_args.input_file
    output_dir: str = output_file or parsed_args.output_file

    if input_dir and os.path.isdir(input_dir):
        input_files = list(map(lambda f: os.path.join(input_dir, f), os.listdir(input_dir)))

        if output_dir and os.path.isdir(output_dir):
            output_files = map(lambda f: os.path.join(output_dir, f), os.listdir(input_dir))
        else:
            output_files = [None] * len(input_files)

        for input_file, output_file in zip(input_files, output_files):
            with InputParameter(*args,
                                input_file=input_file,
                                output_file=output_file,
                                **kwargs) as parameter:
                editor = Editor(parameter)
                editor.execute()
    else:
        with InputParameter(*args,
                            input_file=input_file,
                            output_file=output_file,
                            **kwargs) as parameter:
            editor = Editor(parameter)
            editor.execute()


if __name__ == '__main__':
    main()
