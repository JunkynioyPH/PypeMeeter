import subprocess, time, atexit, rich, enum, os
from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal
class BinaryType(enum.Enum):
    SYSTEM = 0
class NoInletDataError(Exception):
    """Data returned None [DATA IS NOT!]"""
# Maybe for cross-platform... ?
class CommandOSType(enum.Enum):
    NT = []
    UNIX = []
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
class PypeInletPort():
    def __init__(self, name:str, inputDevices:list[str], ffmpeg:BinaryType|str=BinaryType.SYSTEM):
        """
        Args:
            name (str): Displayed input stream name.
            inputDevices (list[str]): list of device names to capture.
            ffmpeg (BinaryType | str, optional): External FFMPEG Binary. Defaults to BinaryType.SYSTEM.
        """
        self.name:str = f"PypeMeeter_Inlet.{name}"
        self.devices:dict[str, int] = inputDevices
        self.ffmpegBinary:BinaryType|str = ffmpeg
        self.process:subprocess.Popen|None = None
        atexit.register(self._exit)
    # Im probably doing something wrong with ehese ffmpeg commands
    # sooo i kept both
    def _command(self, alsa=False):
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        inputs = []
        for device in self.devices:
            # inputs.extend(["-f", 'pulse', '-i', device])
            inputs.extend(["-f", 'pulse', "-fragment_size", "100", '-stream_name', f"PypeMeeter-Inlet_{self.name}", '-i', device])
        input_command = [
            ffmpegBinary,
            '-re', *inputs,
            "-filter_complex", f"amix=inputs={len(self.devices)}:dropout_transition=0",
            "-f", "s16le", "-ac", '2', "-ar", "48000",
            "-fflags", "nobuffer+igndts", "-avioflags", "direct",
            "-fflags", "fastseek", "-flush_packets", "1", 
            "pipe:1"
        ] if not alsa else [
            ... ## TODO
        ]
        print(input_command)
        return input_command
    def _command_old(self) -> list:
        rich.print(f'[PypeMeeter] {self} [yellow]Using Old Inlet Command.')
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        inputs = []
        for device in self.devices:
            inputs.extend(["-f", 'pulse', '-stream_name', f"PypeMeeter-Inlet_{self.name}", '-i', device])
        input_command = [
        ffmpegBinary,
        # "-threads", "1",
        '-re', *inputs, 
        "-filter_complex", f"amix=inputs={len(self.devices)}:dropout_transition=0",
        "-fflags", "nobuffer+igndts", "-avioflags", "direct",
        "-f", "s16le", "-ac", '2', "-ar", "48000",
        "-flush_packets", "1",
        "pipe:1"]  # Write to stdout
        return input_command
    def start(self, alsa=False, oldCommand=False, ffmpegVerbose=False) -> None:
        #NOTE: new command stub
        rich.print(f'[PypeMeeter] [green]Spawned:[/green] {self}')
        command = self._command_old() if oldCommand else self._command(alsa)
        verbose = None if ffmpegVerbose else subprocess.DEVNULL
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=verbose)
    def getData(self, buffer:int=128, channels:int=2) -> bytes:
        chunk = buffer * 2 * channels
        data = self.process.stdout.read(chunk)
        if not data:
            raise NoInletDataError('Check: if not data, FAILED.')
        return data
    def _exit(self):
        self.process.terminate()
        rich.print(f'[PypeMeeter] [red]Terminated:[/red] {self}')
    def __repr__(self):
        return f'<PypeInletPort({self.name}) << {len(self.devices)}_streams>'
class PypeOutletPort():
    def __init__(self, name:str, outputDevice:str, ffmpeg:BinaryType|str=BinaryType.SYSTEM):
        """
        Args:
            name (str): Displayed output stream name.
            outputDevice (str): name of the singular output device.
            ffmpeg (BinaryType | str, optional): External FFMPEG Binary. Defaults to BinaryType.SYSTEM.
        """
        self.name:str = f"PypeMeeter_Outlet.{name}"
        self.device:str = outputDevice
        self.ffmpegBinary:BinaryType|str = ffmpeg
        self.process:subprocess.Popen|None = None
        atexit.register(self._exit)
    # Im probably doing something wrong with ehese ffmpeg commands
    # sooo i kept both
    def _command(self, alsa=False):
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        output_command = [ffmpegBinary, #'-threads', '1',
                          "-fflags", "nobuffer+igndts", "-flush_packets", "1",
                          "-f", "s16le", "-ar", '48000', '-ac', '2', '-i', 'pipe:0',
                          "-f", "pulse", "-device", self.device,
                          "-buffer_size", '512', "-fragment_size", "100",
                          f"PypeMeeter-Outlet{self.name}"] if not alsa else [
                              ... ## TODO
                          ]
        return output_command
    def _command_old(self) -> list:
        rich.print(f'[PypeMeeter] {self} [yellow]Using Old Outlet Command.')
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        output_command = [
            ffmpegBinary,
            #"-threads", "1",
            "-fflags", "nobuffer+igndts",
            "-f", "s16le", "-ac", '2', "-ar", "48000", "-i", "pipe:0",
            "-f", "pulse", "-device", self.device,
            f"PypeMeeter-Outlet{self.name}"]
        return output_command
    def start(self, alsa=False, oldCommand=False, ffmpegVerbose=False):
        #NOTE: new command stub
        rich.print(f'[PypeMeeter] [green]Spawned:[/green] {self}')
        command = self._command_old() if oldCommand else self._command(alsa)
        verbose = None if ffmpegVerbose else subprocess.DEVNULL
        self.process:subprocess.Popen|None = subprocess.Popen(command, bufsize=0, stdin=subprocess.PIPE, stderr=verbose)
    def sendData(self, data:bytes):
        self.process.stdin.write(data)
    def _exit(self):
        self.process.stdin.close()
        self.process.terminate()
        rich.print(f'[PypeMeeter] [red]Terminated:[/red] {self}')
    def __repr__(self):
        return f'<PypeOutletPort({self.name}) >> {self.device}>'

# test the implementation.
if __name__ == "__main__":
    devices = [
        'Soundboard_Playback.monitor',
        'alsa_input.pci-0000_2f_00.4.analog-stereo'
    ]
    # it's a bit weird but i cant get this ffmpeg binary to recognise "-f pulse" or any of the current flags...
    ffmpeg = BinaryType.SYSTEM #'/media/160gbBag/g. software stuff/FFMPEG-8-Linux/ffmpeg'
    pipeIN = PypeInletPort('MicMerge', devices, ffmpeg=ffmpeg)
    pipeOUT = PypeOutletPort('MicMerge', 'Unified_Microphone', ffmpeg=ffmpeg)
    pipeMonitor = PypeOutletPort('MicMergeMonitor', "alsa_output.usb-HP__Inc_HyperX_Cloud_Alpha_S_000000000001-00.analog-surround-71", ffmpeg=ffmpeg)
    pipeIN.start()
    pipeOUT.start()
    pipeMonitor.start()
    
    time.sleep(0.5)
    try:
        while True:
            # only .getData(x) once please, or else it dies when it gets
            # eevery time for new device
            data = pipeIN.getData(4)
            
            pipeOUT.sendData(data)
            pipeMonitor.sendData(data)
            
            # os.system('clear')
            # print(pipeIN, pipeOUT)
    except KeyboardInterrupt:
        rich.print('KEYBOARD INTERRUPT!\nExcept START')
        pipeIN._exit()
        pipeOUT._exit()
        pipeMonitor._exit()
        rich.print('Except END')
        