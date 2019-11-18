#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from PySide2.QtCore import QCoreApplication, QFile, QObject
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QAction, QApplication


class MainForm(QObject):
    """
    Main Window Form
    this class draws the program window
    """

    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        ui_file = QFile(os.path.join(os.path.dirname(__file__),
                                     'messenger.ui'))
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        action_quit = self.window.findChild(QAction, 'action_quit')
        action_quit.triggered.connect(self.quit_application)

        self.window.installEventFilter(self)
        self.window.show()
        self.setParent(self.window)

    def quit_application(self):
        QCoreApplication.quit()


def main():
    app = QApplication(sys.argv)
    main_window = MainForm()
    app.aboutToQuit.connect(main_window.quit_application)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
