## PypeMeeter for Linux Pipewire
This is a work in progress and may or may not eat your ram, because im just a python programmer. /shrug UwU :puke:

This is a program I thought existed, which it does, but they havent updated it or it was just annoying to use or clunky or it breaks each time... not that this program wont either but I trust this more than other's solutions.
I also cannot be bothered to do any more research or compile my own garbage so im making it the way I know how.

This python program utilises FFMPEG.

Whether your system's ffmpeg (ffmpeg) or own ffmpeg binary (.../path/to/ffmpeg) to:
- Capture audio from theoratically any input/monitor(output) device that pipewire can see.
- Playback the stream to whatever audio output device you wish.

The program does this by creating separate subprocesses for input and output nodes, and have input stream written to the output.

This effectively has 2 FFMPEG running, 1 for specifically capturing audio and 1 for specifically outputting to an audio device.
