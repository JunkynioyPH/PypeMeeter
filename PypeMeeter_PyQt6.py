from PyQt6.QtCore import Qt, QTimer, QObject, QThread, pyqtSlot, pyqtSignal

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
        print('[PypeWrench] UpdateTimerQueue: ', end='')
        if not callable(_callable):
            return print(f'Not Callable {_callable}')
        print(f'Appended {_callable}')
        self.updateList.append(_callable)
    def popQueueItem(self, index:int):
        self.updateList.pop(index)