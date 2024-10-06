import os
import stat
import sys

if len(sys.argv) < 2:
    print('install dir needed.')
    exit(-1)

BIN_ROOT = sys.argv[1]

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
print(PROJECT_ROOT)

shebang_line = ''
file_ext = ''
all_args = '$@'
args1 = '$1'
if sys.platform == 'win32':
    activate_env = f'{PROJECT_ROOT}\\venv\\Scripts\\activate.ps1\n'
    file_ext = '.ps1'
    all_args = '$args'
    args1 = '$args[0]'
else:
    activate_env = f'source {PROJECT_ROOT}/venv/bin/activate\n'
    shebang_line = '#!/bin/zsh\n'

link_file = os.path.join(BIN_ROOT, f'jumpcutter{file_ext}')
with open(link_file, 'w') as file:
    file.write(shebang_line)
    file.write(activate_env)
    file.write(f'python3 {PROJECT_ROOT}{os.sep}src{os.sep}jumpcutter.py {all_args}\n')
    file.write('deactivate\n')

short_cut = os.path.join(BIN_ROOT, f'jumpcut{file_ext}')
with open(short_cut, 'w') as file:
    file.write(shebang_line)
    file.write(f'{link_file} --input_file {args1} --silent_speed 9999 --frame_margin 3 '
               f'--keep_start 2 --keep_end 2 --use_hardware_acc 1 --silent_threshold 0.005\n')

os.chmod(link_file, stat.S_IREAD | stat.S_IEXEC | stat.S_IWUSR)
os.chmod(short_cut, stat.S_IREAD | stat.S_IEXEC | stat.S_IWUSR)