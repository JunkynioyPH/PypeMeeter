import time, atexit, rich, enum, os, sys
from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal, QProcess
from PyQt6.QtWidgets import *
OS_NT = os.name=='nt'
class NoInletDataError(Exception):
    """Data returned None [DATA IS NOT!]"""
class BinaryType(enum.Enum):
    SYSTEM  = 0
class AudioSystemType(enum.Enum):
    ALSA    = 'alsa'
    PULSE   = 'pulse'
# Maybe for cross-platform... ?
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
# test the implementation.
class PypeInlet(QProcess):
    def __init__(self, name:str, devices:dict[str, AudioSystemType], ffmpeg:str|BinaryType=BinaryType.SYSTEM, parent=None):
        super().__init__(parent)
        self.setProgram('ffmpeg' if ffmpeg == BinaryType.SYSTEM else os.path.join(str(ffmpeg)))
        self.name = name
        self.streams = len(devices)
        self.inputStreams = []
        if OS_NT is False:
            # Construct the arguments for Linux
            ## 19.07.2026 @ 2:55 AM == Alsa part of this is not tested.
            ### https://ffmpeg.org/ffmpeg-formats.html#Format-stream-specifiers-1
            ### It helps if you actually read the docs :skull:
            for device in devices:
                rich.print(f'[PypeMeeter] PypeInlet({name}): Constructing Args for [magenta]({devices.get(device)}):<{device}>[/magenta]', end=' ')
                commandArgs:list = ['-re', 
                    '-probesize', '32', '-f', str(devices.get(device).value), '-ac', '2', '-ar', '48000',
                    '-fflags', '+fastseek+igndts+nobuffer+nofillin',
                    "-avioflags", "direct", '-analyzeduration', '0',
                    '-fragment_size', '100', '-stream_name', f"PypeMeeter-Inlet_{name}",
                    '-i', str(device)
                    ]
                self.inputStreams.extend(commandArgs)
                rich.print('[green]OK')
            else:
                rich.print(f'[PypeMeeter] PypeInlet({name}): [green]Constructed input stream arguments')
        elif OS_NT is True:
            ### UNVERIFIED
            # Construct the arguments for Windows
            commandArgs:list = [
                '-re', '-f', 'dshow', '-ac', '2', '-ar', '48000', '-fragment_size', '100'
            ]
            ### TODO ...
            raise NotImplementedError("This is not yet functional")
        else:
            raise NotImplementedError(f'[PypeMeeter] No idea what "{os.name}" is!')
        
        # if needed, amix=inputs=X:duration= shortest | longest
        self.command = [
            # input flags device from devices
            *self.inputStreams,
            
            # mixer flags for mixing multiple input devices
            "-filter_complex", f"amix=inputs={len(devices)}:duration=shortest:dropout_transition=0,aresample=async=1",
            
            # output related flags to pipe
            "-f", "s16le", "-ac", '2', "-ar", "48000",
            "-fflags", "+fastseek+nobuffer+igndts+noparse+nofillin+flush_packets", "-flush_packets", "1", 
            "-avioflags", "direct",
            "pipe:1"
        ]
        self.setArguments(self.command)
        # rich.print(self.command)
    def stopPype(self):
        self.terminate()
        rich.print(f"[PypeMeeter] Terminated {self}")
    def __repr__(self):
        return f'<PypeInlet({self.name}).{self.program()}.{self.streams}_Streams>'
    
class PypeOutlet(QProcess):
    def __init__(self, name:str, device:str, ffmpeg:str|BinaryType=BinaryType.SYSTEM, parent=None):
        super().__init__(parent)
        self.setProgram('ffmpeg' if ffmpeg == BinaryType.SYSTEM else os.path.join(str(ffmpeg)))
        self.name, self.device = name, device
        self.command = [#'-threads', '2', s16le
                        # input related flags from pipe:0
                        "-f", "s16le", "-ar", '48000', '-ac', '2', 
                        "-fflags", "+fastseek+nobuffer+igndts+nofillin",
                        '-avioflags', 'direct',
                        '-i', 'pipe:0',
                        
                        # output related flags to device
                        "-f", "pulse", "-device", device,
                        '-fflags', '+nobuffer+fastseek+igndts+noparse+nofillin+flush_packets',
                        "-flush_packets", "1",
                        "-buffer_size", '512', "-fragment_size", "100",
                        # '-af','asubboost=boost=12',
                        f"PypeMeeter-Outlet{name}"]
        self.setArguments(self.command)
    def stopPype(self):
        self.terminate()
        rich.print(f"[PypeMeeter] Terminated {self}")
    def __repr__(self):
        return f'<PypeOutlet({self.name}).{self.program()}.{self.device}>'
        
class PypeFilter(QProcess):
    ...
class PypeManager():
    ...
    
        # AudioSystemType.ALSA:'hw:0,0',
if __name__ == '__main__':
    APP = QApplication([])
    inletTest = PypeInlet('PypeTest', {
        'Soundboard_Playback.monitor':AudioSystemType.PULSE,
        'alsa_input.pci-0000_2f_00.4.analog-stereo':AudioSystemType.PULSE
    })
    outletTest = PypeOutlet('PypeTest', "alsa_output.usb-HP__Inc_HyperX_Cloud_Alpha_S_000000000001-00.analog-surround-71")
    inletTest.setStandardOutputProcess(outletTest)
    
    #### THIS FOR SOME REASON BLOCKS THE WHOLE THING, 
    #### BUT AUDIO STREAMS WORK WHEN COMMENTED OUT SO I WONT COMPLAIN
    #### This started when i started to add more -fflag args from both in/out commands
    ##
    # inletTest.readyReadStandardError.connect(lambda: os.system('clear'))
    # inletTest.readyReadStandardError.connect(lambda: rich.print("[green] INLET INFO:", bytes(inletTest.readAllStandardError()).decode()))
    # outletTest.readyReadStandardError.connect(lambda: rich.print("[red]OUTLET INFO:", bytes(outletTest.readAllStandardError()).decode()))
    
    
    outletTest.start()
    inletTest.start()
    
    updateLoop = updateTimerQueue(ticks=128)
    # APP.aboutToQuit.connect(inletTest.stopPype) ## Will have to figure out a way to make sure everything gets terminated properly
    # APP.aboutToQuit.connect(inletTest.stopPype())
    sys.exit(APP.exec())