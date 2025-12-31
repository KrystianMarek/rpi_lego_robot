#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K.O.C Robot GUI Client

Environment variables:
    ROBOT_IP - Robot's IP address (default: empty, must enter in GUI)

See app/common/config.py for all configuration options.
"""
import signal
import sys
import warnings

# Suppress numpy deprecation warning from pickle (server has older numpy)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='pickle')

# Load .env file if python-dotenv is available (before importing Config)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars only

from PyQt5.QtWidgets import QApplication, QMainWindow

from app.client.gui.MainWindowWrapper import MainWindowWrapper
from app.common.config import Config
from app.common.LoggingWrapper import setup_logging


def launch_gui():
    app = QApplication(sys.argv)
    main_window = QMainWindow()

    wrapper = MainWindowWrapper(app, main_window, default_robot_ip=Config.ROBOT_IP)

    # Handle Ctrl+C gracefully
    def sigint_handler(*args):
        print("\nCtrl+C pressed, disconnecting...")
        wrapper.cleanup()
        app.quit()

    signal.signal(signal.SIGINT, sigint_handler)

    # Allow Python to handle signals (required for Ctrl+C in Qt)
    # Timer triggers event loop to check for signals
    from PyQt5.QtCore import QTimer
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)  # Just keep event loop alive
    signal_timer.start(100)

    main_window.show()
    sys.exit(app.exec_())


def main():
    setup_logging()
    launch_gui()


if __name__ == '__main__':
    main()
