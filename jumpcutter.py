from editor import Editor
from parameters import InputParameter


def main(*args, **kwargs):
    with InputParameter(*args, **kwargs) as parameter:
        editor = Editor(parameter)
        editor.execute()


if __name__ == '__main__':
    main()
