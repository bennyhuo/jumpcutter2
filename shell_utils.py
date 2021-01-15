import subprocess

STRING = -1


def do_shell(command, stdout=None, encoding=None):
    print(f"[Shell] {command}")
    if stdout == STRING:
        return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding=encoding).stdout
    else:
        subprocess.run(command, shell=True, stdout=stdout, encoding=encoding)
