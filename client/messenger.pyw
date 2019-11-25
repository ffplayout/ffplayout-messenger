#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import glob
import json
import logging
import os
import re
import requests
import sys
from functools import partial
from logging.handlers import TimedRotatingFileHandler
from platform import system
from queue import Queue
from subprocess import PIPE, Popen
from time import sleep
from types import SimpleNamespace

import zmq
from PySide2.QtCore import (QCoreApplication, QFile, QObject, QThread, Signal,
                            Slot, Qt)
from PySide2.QtGui import QIcon
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QAction, QApplication, QCheckBox, QColorDialog,
                               QComboBox, QDialog, QInputDialog, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QSpinBox,
                               QTextEdit, QTextBrowser, QDialogButtonBox,
                               QVBoxLayout)

cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), 'assets', 'messenger.ini'))

_preview = SimpleNamespace(
    color=cfg.get('PREVIEW', 'color'),
    clip=cfg.get('PREVIEW', 'clip'),
    width=cfg.get('PREVIEW', 'width'),
    height=cfg.get('PREVIEW', 'height'),
    font=cfg.get('PREVIEW', 'font'),
    ffplay=cfg.get('PREVIEW', 'ffplay'),
    port=cfg.getint('PREVIEW', 'port')
)

_log = SimpleNamespace(
    level=cfg.get('LOGGING', 'log_level'),
    path=os.path.join(os.path.dirname(__file__), 'log', 'messenger.log')
)

_server = SimpleNamespace(
    address=cfg.get('SERVER', 'address'),
    port=cfg.getint('SERVER', 'port'),
    user=cfg.get('SERVER', 'user'),
    password=cfg.get('SERVER', 'password')
)

# check if log folder exists and create it if not
if not os.path.isdir(os.path.dirname(_log.path)):
    os.mkdir(os.path.dirname(_log.path))


logger = logging.getLogger('messenger')
logger.setLevel(_log.level)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]  %(message)s')
file_handler = TimedRotatingFileHandler(_log.path, when='midnight',
                                        backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Worker(QObject):
    """
    preview worker thread,
    here we start ffplay for previewing drawtext
    """

    std_error = Signal(str)

    def __init__(self, queue):
        QObject.__init__(self)
        self.is_running = True
        self._proc = None
        self._queue = queue

        if _preview.clip:
            self.input = ['-i', _preview.clip]
        else:
            self.input = ['-f', 'lavfi', 'color=s={}x{}:c={}'.format(
                _preview.width, _preview.height, _preview.color)]

    def work(self):
        while self.is_running:
            run = self._queue.get()
            if run:
                win_arg = {}
                if system() == "Windows":
                    # prevent terminal open
                    win_arg['creationflags'] = 0x08000000

                drawt = "drawtext=text='':fontfile='{}'".format(_preview.font)
                cmd = ([_preview.ffplay, '-hide_banner', '-nostats',
                        '-v', 'error']
                       + self.input + ['-vf', "scale='{}:{}',zmq,{}".format(
                        _preview.width, _preview.height, drawt)])
                self._proc = Popen(cmd, stderr=PIPE, **win_arg)

                for line in self._proc.stderr:
                    if 'Last message repeated' not in line.decode():
                        self.std_error.emit(line.decode().strip())

            sleep(0.5)

    def quit(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self.is_running = False


class Examples(QDialog):
    """
    Examples Window
    """

    def __init__(self, parent):
        super(Examples, self).__init__(parent)
        self.setWindowTitle("Some Examples")
        self.resize(500, 340)
        self.setSizeGripEnabled(True)

        text = (
            '<h3>Text Functions:</h3>'
            '<strong>burn timecode: </strong>'
            '%{pts\\:gmtime\\:0\\:%H\\\\\\:%M\\\\\\:%S}'
            '<br />'
            '<strong>print date and time: </strong>'
            '%{localtime\\:%a %b %d %Y %H\\\\\\:%M\\\\\\:%S}'
            '<br />'

            )

        self.info = QTextBrowser()
        self.info.setHtml(text)
        self.button = QDialogButtonBox()
        self.button.setOrientation(Qt.Horizontal)
        self.button.setStandardButtons(QDialogButtonBox.Ok)
        self.button.clicked.connect(self.close_examples)

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.info)
        layout.addWidget(self.button)

        # Set dialog layout
        self.setLayout(layout)

    def close_examples(self):
        self.close()


class MainForm(QObject):
    """
    Main Window Form
    this class draws the program window
    """

    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        self.root_path = os.path.dirname(__file__)
        ui_file = QFile(os.path.join(self.root_path, 'assets', 'messenger.ui'))
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        self.preset = None

        action_quit = self.window.findChild(QAction, 'action_quit')
        action_quit.triggered.connect(self.quit_application)
        action_save = self.window.findChild(QAction, 'action_save')
        action_save.triggered.connect(self.save_preset)
        action_save = self.window.findChild(QAction, 'action_examples')
        action_save.triggered.connect(self.open_examples)

        # form content
        self.text = self.window.findChild(QTextEdit, 'text_area')
        self.pos_x = self.window.findChild(QLineEdit, 'text_x_pos')
        self.pos_y = self.window.findChild(QLineEdit, 'text_y_pos')
        self.font_size = self.window.findChild(QSpinBox, 'spin_font_size')
        self.line_spacing = self.window.findChild(QSpinBox,
                                                  'spin_line_spacing')

        self.font_color = self.window.findChild(QPushButton,
                                                'botton_font_color')
        self.font_color_preview = self.window.findChild(QLabel,
                                                        'label_font_color')
        self.font_color.setStyleSheet("background-color: #fff;")

        self.font_color_t = self.window.findChild(QLineEdit, 'text_font_color')
        self.font_color_t.setText('#ffffff')
        self.alpha = self.window.findChild(QLineEdit, 'text_alpha')

        self.show_box = self.window.findChild(QCheckBox, 'activate_box')
        self.box_color = self.window.findChild(QPushButton, 'botton_box_color')
        self.box_color.setStyleSheet("background-color: #000;")
        self.box_color_t = self.window.findChild(QLineEdit, 'text_box_color')
        self.box_color_t.setText('#000000')
        self.border_w = self.window.findChild(QSpinBox, 'spin_border_width')

        self.font_color.clicked.connect(partial(self.change_color,
                                                self.font_color,
                                                self.font_color_t))
        self.box_color.clicked.connect(partial(self.change_color,
                                               self.box_color,
                                               self.box_color_t))

        self.combo = self.window.findChild(QComboBox, 'combo_presets')
        self.combo.currentIndexChanged.connect(self.preset_selector)

        self.save = self.window.findChild(QPushButton, 'button_save')
        self.save.clicked.connect(self.save_preset)

        self.play = self.window.findChild(QPushButton, 'button_preview')
        self.play.clicked.connect(self.preview_text)

        self.send = self.window.findChild(QPushButton, 'button_send')
        self.send.clicked.connect(self.send_request)

        # preview worker
        self.filter_queue = Queue()
        self.worker = Worker(self.filter_queue)
        self.worker_thread = QThread()
        self.worker_thread.started.connect(self.worker.work)
        self.worker.moveToThread(self.worker_thread)
        self.worker.std_error.connect(self.preview_log)

        # zmq sender
        self.context = zmq.Context()

        self.list_presets()

        self.window.installEventFilter(self)
        self.window.show()
        self.setParent(self.window)

    @Slot(str)
    def preview_log(self, log):
        logger.error(log)
        self.show_dialog(
            'error', '<strong>drawtext syntax error:</strong><br /> {}'.format(
                log))

    def show_dialog(self, level, message):
        """
        Show the information, warning and critical message
        """
        if level == "error":
            QMessageBox.critical(self.window, "Error", message)
        if level == "info":
            QMessageBox.information(self.window, "Information", message)
        if level == "warning":
            QMessageBox.warning(self.window, "Warning", message)

    def open_examples(self):
        examples = Examples(self.window)
        examples.show()

    def change_color(self, btn, text):
        color = QColorDialog.getColor(initial='#ffffff', parent=None,
                                      title='Select Color',
                                      options=QColorDialog.ShowAlphaChannel)

        if color.isValid():
            btn.setStyleSheet(
                "background-color: {}".format(color.name()))
            text.setText('{}@0x{:02x}'.format(color.name(), color.alpha()))

    def check_empty(self, key, value):
        if not value:
            self.show_dialog('warning', 'Value "{}" is empty!'.format(key))

    def set_content(self, preset):
        self.text.clear()
        self.text.insertPlainText(preset['text'])
        self.pos_x.setText(preset['x'])
        self.pos_y.setText(preset['y'])
        self.font_size.setValue(preset['fontsize'])
        self.line_spacing.setValue(preset['line_spacing'])
        self.font_color.setStyleSheet(
            "background-color: {};".format(
                preset['fontcolor'].split('@')[0]))
        self.font_color_t.setText(preset['fontcolor'])
        self.alpha.setText(preset['alpha'])
        self.show_box.setChecked(preset['box'])
        self.box_color.setStyleSheet(
            "background-color: {};".format(
                preset['boxcolor'].split('@')[0]))
        self.box_color_t.setText(preset['boxcolor'])
        self.border_w.setValue(preset['boxborderw'])

    def get_content(self):
        if re.match(r'.*%{.*}.*', self.text.toPlainText()):
            text_fmt = self.text.toPlainText()
        else:
            text_fmt = self.text.toPlainText().replace('\\', '\\\\\\\\')\
                .replace("'", "\u2019")\
                .replace(' ', '\\ ').replace('%', '\\\\%').replace(':', '\\:')

        self.check_empty('X', self.pos_x.text())
        self.check_empty('Y', self.pos_y.text())
        self.check_empty('fontsize', self.font_size.value())
        self.check_empty('alpha', self.alpha.text())

        content = {
            'text': text_fmt,
            'x': self.pos_x.text(),
            'y': self.pos_y.text(),
            'fontsize': self.font_size.value(),
            'line_spacing': self.line_spacing.value(),
            'fontcolor': self.font_color_t.text(),
            'alpha': self.alpha.text(),
            'box': 1 if self.show_box.isChecked() else 0,
            'boxcolor': self.box_color_t.text(),
            'boxborderw': self.border_w.value()
        }

        return content

    def list_presets(self):
        self.combo.clear()
        presets = []
        index = 0

        for idx, preset in enumerate(sorted(glob.glob(
                os.path.join(self.root_path, 'presets', '*.json')))):
            name = os.path.basename(preset)
            presets.append(name)

            if name.rstrip('.json') == self.preset:
                index = idx

        self.combo.addItems(presets)
        self.combo.setCurrentIndex(index)

    def preset_selector(self, idx):
        preset = self.combo.itemText(idx)

        if preset:
            with open(os.path.join(self.root_path, 'presets', preset)) as f:
                self.set_content(json.load(f))

    def preview_text(self):
        filter_str = ''
        if not self.worker_thread.isRunning():
            self.worker_thread.start()

        if self.filter_queue.empty():
            self.filter_queue.put(True)
            self.filter_queue.put(False)

        sleep(0.5)

        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:{}".format(_preview.port))

        for key, value in self.get_content().items():
            filter_str += "{}='{}':".format(key, value)

        logger.debug(filter_str)

        socket.send_string(
            "Parsed_drawtext_2 reinit " + filter_str.rstrip(':'))

        message = socket.recv()
        logger.info("Received reply: {}".format(message.decode()))

    def save_preset(self):
        preset, ok = QInputDialog.getText(self.window, 'Save Preset',
                                          'Enter preset name:')

        if ok:
            content = self.get_content()
            self.preset = preset.rstrip('.json')

            with open(
                os.path.join(self.root_path, 'presets', self.preset + '.json'
                             ), 'w') as outfile:
                json.dump(content, outfile, indent=4)

            self.list_presets()

    def send_request(self):
        content = self.get_content()

        try:
            r = requests.post('{}:{}'.format(_server.address, _server.port),
                              json={"user": _server.user,
                                    "password": _server.password,
                                    "data": content
                                    },
                              verify=False, timeout=1.5)

            if r.status_code == 200:
                self.show_dialog('info', 'sending success')
            else:
                self.show_dialog('error', 'sending failed')

            logger.info(r.status_code)
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout):
            self.show_dialog('error', 'Send drawtext command timeout!')
            logger.error('Send drawtext command timeout!')

    def quit_application(self):
        self.worker.quit()
        self.worker_thread.quit()
        self.worker_thread.wait()
        QCoreApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(
        QIcon(os.path.join(os.path.dirname(__file__), 'assets',
                           'messenger.ico')))

    main_window = MainForm()
    app.aboutToQuit.connect(main_window.quit_application)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
