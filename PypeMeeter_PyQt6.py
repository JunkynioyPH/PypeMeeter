from rich import pretty
pretty.install()
import json, os, sys, rich
from PyQt6.QtCore import Qt, QTimer, QObject, QEvent, QThread, pyqtSlot, pyqtSignal
from PyQt6.QtMultimedia import QMediaDevices
from PyQt6.QtWidgets import *