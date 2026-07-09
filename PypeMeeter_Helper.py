import subprocess, time, atexit, rich, enum
from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal
class FfmpegBinarySourceType(enum.Enum):
    SYSTEM = 0
    LOCALPATH = 1
    
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
    def __init__(self, inletName:str, inputDevices:dict[str, int], ffmpeg:FfmpegBinarySourceType=FfmpegBinarySourceType.SYSTEM):
        pass
    def _ffmpegCaptureCommand(self):
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