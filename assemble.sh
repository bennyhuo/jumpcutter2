WORKING_DIR=$(cd $(dirname $0) && pwd -P)
cd $WORKING_DIR
pwd

pip3 install -r requirements.txt
pyinstaller jumpcutter.py --onefile

# copy ffmpeg
cp $(ls $(which ffmpeg)) dist/ 

cd -