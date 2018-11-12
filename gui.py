#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from app.client.gui.MainWindowWrapper import MainWindowWrapper
from app.common.LoggingWrapper import setup_logging


def launch_gui():
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    wrapper = MainWindowWrapper(app, main_window)
    main_window.show()
    # wrapper.connect()
    sys.exit(app.exec_())


def main():
    setup_logging()
    launch_gui()


if __name__ == '__main__':
    main()
