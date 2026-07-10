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
    # {'deviceName':channelCountInteger}
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
    def _captureCommand_old(self) -> list:
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        inputs = []
        for device in self.devices:
            inputs.extend(["-f", 'pulse', '-stream_name', f"PypeMeeter-Inlet_{self.name}", '-i', device])
        input_command = [
        ffmpegBinary,
        "-threads", "1",
        '-re', *inputs, 
        "-filter_complex", f"amix=inputs={len(self.devices)}:dropout_transition=0",
        "-fflags", "nobuffer+igndts", "-avioflags", "direct",
        "-f", "s16le", "-ac", '2', "-ar", "48000",
        "-flush_packets", "1",
        "pipe:1"]  # Write to stdout
        return input_command
    def start(self, oldCommand=False, ffmpegVerbose=False) -> None:
        #NOTE: new command stub
        rich.print(f'[PypeMeeter] [green]Spawned:[/green] {self}')
        command = self._captureCommand_old() if oldCommand else print('NEW COMMAND SOON')
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
    def _playbackCommand_old(self) -> list:
        ffmpegBinary = "ffmpeg" if self.ffmpegBinary is BinaryType.SYSTEM else self.ffmpegBinary
        output_command = [
            ffmpegBinary,
            "-threads", "1",
            "-fflags", "nobuffer",
            "-f", "s16le", 
            "-ac", '2', 
            "-ar", "48000",
            "-i", "pipe:0",
            "-f", "pulse",
            "-device", self.device,
            f"PypeMeeter-Outlet{self.name}"]
        return output_command
    def start(self, oldCommand=False, ffmpegVerbose=False):
        #NOTE: new command stub
        rich.print(f'[PypeMeeter] [green]Spawned:[/green] {self}')
        command = self._playbackCommand_old() if oldCommand else print('NEW COMMAND SOON')
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
        
if __name__ == "__main__":
    devices = [
        'Soundboard_Playback.monitor',
        'alsa_input.pci-0000_2f_00.4.analog-stereo'
    ]
    pipeIN = PypeInletPort('MicMerge', devices)
    pipeOUT = PypeOutletPort('MicMerge', 'Unified_Microphone')
    pipeIN.start(True)
    pipeOUT.start(True)
    time.sleep(0.5)
    while True:
        pipeOUT.sendData(pipeIN.getData(4))
        # os.system('clear')
        # print(pipeIN, pipeOUT)