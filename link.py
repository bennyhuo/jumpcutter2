import os
import stat
import sys

if len(sys.argv) < 2:
    print('install dir needed.')
    exit(-1)

BIN_ROOT = sys.argv[1]

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
print(PROJECT_ROOT)

filename = "jumpcut.ps1" if sys.platform == 'win32' else "jumpcut"

target_path = os.path.join(BIN_ROOT, filename)
with open(os.path.join(PROJECT_ROOT, "template", filename), 'r') as source_file:
    with open(target_path, 'w') as target_file:
        target_file.write(source_file.read().replace("{{SCRIPT_ROOT}}", PROJECT_ROOT))

os.chmod(target_path, stat.S_IREAD | stat.S_IEXEC | stat.S_IWUSR)