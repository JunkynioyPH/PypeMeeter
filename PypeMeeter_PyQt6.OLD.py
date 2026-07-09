from PyQt6.QtCore import Qt, QTimer, QObject
import os, atexit, subprocess, rich, time
def ffmpegCaptureCommand(name:str, inDevices:list, channels:int=2, ffmpegPath:str|None=None) -> list:
    ffmpegBinary = "ffmpeg" if ffmpegPath is None else ffmpegPath
    inputs = []
    for each in inDevices:
        inputs.extend(["-f", 'pulse', '-stream_name', f"PypeMeeter-Capture_{name}", '-i', each])
    else:
        rich.print(f'[green]{inputs}')
    # pos 8
    input_command = [
    ffmpegBinary,
    "-threads", "1",
    # "-thread_queue_size", "4",
    '-re', *inputs, 
    "-filter_complex", f"amix=inputs={len(inDevices)}:dropout_transition=0",
    "-fflags", "nobuffer+igndts", "-avioflags", "direct",
    "-f", "s16le", "-ac", f"{channels}", "-ar", "48000",
    "-flush_packets", "1",
    "pipe:1"  # Write to stdout
    ]
    return input_command
def ffmpegPlaybackCommand(name:str, outDevice:str, channels:int=2, ffmpegPath:str|None=None) -> list:
    ffmpegBinary = "ffmpeg" if ffmpegPath is None else ffmpegPath
    output_command = [
        ffmpegBinary,
        "-threads", "1",               # Force single-threading
        "-fflags", "nobuffer",         # Disable input buffering
        # "-thread_queue_size", "4",    # Strictly limit the input pipe RAM buffer
        "-f", "s16le", 
        "-ac", f"{channels}", 
        "-ar", "48000",
        "-i", "pipe:0",                 # Read raw PCM from stdin
        # "-buffer_duration", "2000",        # 2ms hardware buffer duration (low latency/RAM)
        "-f", "pulse",                  # Output muxer format
        "-device", outDevice, # The actual output device/sink destination
        f"PypeMeeter-Playback_{name}"
    ]
    return output_command

# Just in case i need it.
class updateTimerQueue(QTimer):
    def __init__(self, parent=None, ticks:int|None=None):
        super().__init__(parent)
        self.updateList:list = []
        self.timeout.connect(self.update)
        self.start(ticks) if ticks else self.start(250)
    def update(self):
        for item in self.updateList:
            item()
    def appendToQueue(self, _callable):
        print('[PypeMeeter] UpdateTimerQueue: ', end='')
        if not callable(_callable):
            return print(f'Not Callable {_callable}')
        print(f'Appended {_callable}')
        self.updateList.append(_callable)
    def popQueueItem(self, index:int):
        self.updateList.pop(index)
class PypePipeObject():
    def __init__(self, name:str, inputs:list[str]|None=None, output:str|None=None):
        self.inputDevices:list[str]|None = inputs if inputs is not None else ['default']
        self.outputDevice:str|None = output if output is not None else ['default']
        self.name = name
        self.subprocesses:dict[str, subprocess.Popen] = {}
        # if not os.path.exists(str(self.name)):
        #     os.mkfifo(self.name)
    def _startCaptureProcess(self):
        command = ffmpegCaptureCommand(self.name, self.inputDevices, 2)
        # print(command)
        self.subprocesses[f'Capture_{self.name}'] = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    def _startPlaybackProcess(self):
        command = ffmpegPlaybackCommand(self.name, self.outputDevice, 2)
        self.subprocesses[f'Playback_{self.name}'] = subprocess.Popen(command, bufsize=0, stdin=subprocess.PIPE )
    def _terminateSubprocesses(self):
        self.subprocesses[f"Capture_{self.name}"].terminate()
        self.subprocesses[f"Playback_{self.name}"].stdin.close()
        self.subprocesses[f"Playback_{self.name}"].terminate()
    def start(self):
        self._startCaptureProcess()
        self._startPlaybackProcess()
        time.sleep(0.5)
        try:
            chunk_size = 8 * 2 * 2
            atexit.register(self._terminateSubprocesses)
            while True:
                data = self.subprocesses[f'Capture_{self.name}'].stdout.read(chunk_size)
                if not data:
                    rich.print('[red] Uh oh! data is not! :()')
                    break
                self.subprocesses[f'Playback_{self.name}'].stdin.write(data)
        except KeyboardInterrupt:
            rich.print("[cyan]\nTerminating FFMPEG processes...")
            self._terminateSubprocesses()
        finally:
            rich.print("[red]\nTerminated FFMPEG processes.")


# For some fking reason Soundboard_Device is seen as Unified_Mic_Device... idk why
PypePipe = PypePipeObject('MicMerge',[
                                'Soundboard_Playback.monitor',
                                'alsa_input.pci-0000_2f_00.4.analog-stereo',
                                # 'alsa_input.usb-HP__Inc_HyperX_DuoCast_202011110001-00.analog-stereo'
                                ],
                          'Unified_Microphone')
PypePipe.start()
    