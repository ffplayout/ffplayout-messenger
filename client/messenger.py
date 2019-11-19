#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from functools import partial

from PySide2.QtCore import QCoreApplication, QFile, QObject
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QAction, QApplication, QPushButton, QTextEdit,
                               QLineEdit, QSpinBox, QCheckBox, QColorDialog,
                               QLabel)


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
        action_save = self.window.findChild(QAction, 'action_save')
        action_save.triggered.connect(self.save_preset)

        # form content
        self.text = self.window.findChild(QTextEdit, 'text_area')
        self.pos_x = self.window.findChild(QLineEdit, 'text_x_pos')
        self.pos_y = self.window.findChild(QLineEdit, 'text_y_pos')

        self.font_color = self.window.findChild(QPushButton,
                                                'botton_font_color')
        self.font_color_preview = self.window.findChild(QLabel,
                                                        'label_font_color')
        self.font_color.setStyleSheet("background-color: #fff; border: 0px;")

        self.font_color_t = self.window.findChild(QLineEdit, 'text_font_color')
        self.font_color_t.setText('#ffffff')
        self.font_size = self.window.findChild(QSpinBox, 'spin_font_size')
        self.alpha = self.window.findChild(QLineEdit, 'text_alpha')

        self.show_box = self.window.findChild(QCheckBox, 'activate_box')
        self.box_color = self.window.findChild(QPushButton, 'botton_box_color')
        self.box_color.setStyleSheet("background-color: #000; border: 0px;")
        self.box_color_t = self.window.findChild(QLineEdit, 'text_box_color')
        self.box_color_t.setText('#000000')
        self.border_w = self.window.findChild(QSpinBox, 'spin_border_width')
        self.border_c = self.window.findChild(QPushButton,
                                              'botton_border_color')
        self.border_c.setStyleSheet("background-color: #000; border: 0px;")
        self.border_c_t = self.window.findChild(QLineEdit, 'text_border_color')
        self.border_c_t.setText('#000000')

        self.font_color.clicked.connect(partial(self.change_font_color,
                                                self.font_color,
                                                self.font_color_t))
        self.box_color.clicked.connect(partial(self.change_font_color,
                                               self.box_color,
                                               self.box_color_t))
        self.border_c.clicked.connect(partial(self.change_font_color,
                                              self.border_c,
                                              self.border_c_t))

        self.save = self.window.findChild(QPushButton, 'button_save')
        self.save.clicked.connect(self.save_preset)

        self.window.installEventFilter(self)
        self.window.show()
        self.setParent(self.window)

    def change_font_color(self, btn, label):
        color = QColorDialog.getColor()
        if color.isValid():
            btn.setStyleSheet(
                "background-color: {}; border: 0px;".format(color.name()))
            label.setText(color.name())

    def get_content(self):
        print(dir(self.text))
        content = {
            'text': self.text.toPlainText(),
            'x': self.pos_x.text(),
            'y': self.pos_y.text(),
            'font_color': self.font_color_t.text(),
            'font_size': self.font_size.value(),
            'alpha': self.alpha.text(),
            'show': self.show_box.isChecked(),
            'box_color': self.box_color_t.text(),
            'border_width': self.border_w.value(),
            'border_color': self.border_c_t.text()
        }

        return content

    def save_preset(self):
        print(self.get_content())

    def quit_application(self):
        QCoreApplication.quit()


def main():
    app = QApplication(sys.argv)
    main_window = MainForm()
    app.aboutToQuit.connect(main_window.quit_application)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
