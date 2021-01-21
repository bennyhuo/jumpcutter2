import subprocess
import os, sys


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


STRING = -1
WORKING_DIR = get_script_path()
ENV = os.environ.copy()
ENV['PATH'] = f"{ENV['PATH']}{os.pathsep}{WORKING_DIR}"


def do_shell(command, stdout=None, encoding=None):
    print(f"[Shell] {command}")
    if stdout == STRING:
        return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding, cwd=WORKING_DIR, env=ENV).stdout
    else:
        subprocess.run(command, shell=True, stdout=stdout, encoding=encoding, cwd=WORKING_DIR, env=ENV)
