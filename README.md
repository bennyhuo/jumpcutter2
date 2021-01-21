# jumpcutter2

Automatically edits videos. Explanation here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Description

**This tool originates from [jumpcutter](https://github.com/carykh/jumpcutter) by carykh.** 

It can be used to cut or speed up/down the silence parts of any videos you want. It is quite useful when you are a tutorial or a vlog maker. Check out the video above to see what it can do.

## How to use

1. Install python 3.
2. Install pip.
3. Run `pip install -r requirements.txt` to install all the dependencies in the shell(or cmd/powershell on Windows). If it complains about 'no such program called pip', try pip3 instead.
4. Run `python jumpcutter.py --input_file input.mp4 --output_file output.mp4 --silent_speed 99999` to cut the video immediately. 
5. Run `python jumpcutter.py --input_file input.mp4 --output_file output.edl --output_type edl --silent_speed 99999` if you want to generate the edl file for later edit. I have tested the edl file in Adobe Premiere and it works.

## What did I do

The original python code from [jumpcutter](https://github.com/carykh/jumpcutter) by carykh runs quite well but it is a bit difficult to add more features to it. So I did some refactor work at first. 

And, added some supports for edl file generating.

Finally, simplified the audio/video processing the make it run faster. 

If you have any question, feel free to open an issue.
