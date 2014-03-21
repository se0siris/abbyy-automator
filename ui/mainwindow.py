from collections import deque
from glob import iglob
import os
import re
from shutil import move
from PyQt4.QtCore import pyqtSignature, QTimer, QThread
from PyQt4.QtGui import QMainWindow, QApplication, QIcon
import time
import sys
from ui.Ui_mainwindow import Ui_MainWindow
from ui.abbyy_controller import AcrobatProxyListener, AbbyyOcr
from ui.custom_widgets import Win7Taskbar, FileWatcher
from ui.message_boxes import message_box_error

__author__ = 'Gary Hughes'


regex_html_tags = re.compile('<[^<]+?>')  # Strip HTML tags.


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class for main application window.
    """

    def __init__(self, parent=None):
        """
        Main application window.
        """
        QMainWindow.__init__(self, parent)

        self.win7_taskbar = Win7Taskbar(self)
        self.app = QApplication.instance()
        self.setupUi(self)
        self.progress_bar.setVisible(0)
        self.on_tb_refresh_profiles_released()

        self.last_logged_text = ''

        self.file_watcher = None
        self.processed_count = -1  # Start at -1 so that the first increment resets to 0.
        self.file_queue = deque()
        self.current_pathname = None
        self.current_watch_path = None

        self.acrobat_proxy_listener = AcrobatProxyListener()
        self.acrobat_proxy_listener.new_path.connect(self.path_received)

        self.abbyy_ocr = AbbyyOcr()
        self.abbyy_ocr.error.connect(self.error_received)

        self.queue_size_changed(0)
        self.statusbar.update_left('Ready to begin')
        self.increment_processed()

    def increment_processed(self):
        self.processed_count += 1
        if self.processed_count == 1:
            self.statusbar.update_middle('1 file processed')
        else:
            self.statusbar.update_middle('{0:,} files processed'.format(self.processed_count))
        self.queue_size_changed(len(self.file_queue))

    def log(self, text='', indent=False, update_existing=False, colour=None, bold=False, status_bar=False):
        """
        Update the QPlainTextEdit based log.
        """
        if colour:
            if colour == 'green':
                text = '<font color="#347235">%s</font>' % text
            elif colour == 'red':
                text = '<font color="#7E2217">%s</font>' % text
        if bold:
            text = '<b>%s</b>' % text
        if indent or update_existing:
            text = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s' % text
        if update_existing:
            self.pte_log.undo()
            text = '%s%s' % (self.last_logged_text, text)

        self.pte_log.appendHtml(text)
        self.last_logged_text = text
        self.app.processEvents()
        v_scrollbar = self.pte_log.verticalScrollBar()
        v_scrollbar.setValue(v_scrollbar.maximum())

        if status_bar:
            # Remove HTML tags from the text and add to the status bar.
            self.statusbar.showMessage(regex_html_tags.sub('', text))

    def queue_size_changed(self, count):
        if count == 1:
            self.statusbar.update_right('1 file remaining')
        else:
            self.statusbar.update_right('{0:,} files remaining'.format(count))

        # If we've items in the queue, we're in process mode and currently are not processing any files then start
        # on the next item in the queue.
        if count and self.button_start.isChecked() and not self.current_pathname:
            self.process_next()

    def queue_received(self, queue_list):
        print 'Received new queue'
        length = len(queue_list)
        self.file_queue = deque(queue_list)
        self.log('Found <b>{0:,} files'.format(length))

        self.progress_bar.setRange(0, length)

        if self.button_start.isChecked():
            self.log()
            self.log('Processing queue', bold=True)
            self.log()
            self.process_next()

    def adjust_progress_bars(self):
        self.progress_bar.setMaximum(len(self.file_queue))

    def watch_folder_changed(self, event):
        print event
        action, filename = event
        if action == 3:
            # Updated.
            return
        elif action in (1, 4):
            # Created / Renamed from something.
            self.file_queue.append(filename)
        elif action in (2, 5):
            # Deleted / Renamed to something.
            try:
                self.file_queue.remove(filename)
            except ValueError:
                print 'Error removing from queue:', filename
        self.queue_size_changed(len(self.file_queue))
        self.adjust_progress_bars()

    def process_next(self):
        """
        Get next item in the queue and send it to ABBYY.
        """
        try:
            path = self.file_queue.popleft()
        except IndexError:
            # Queue is empty.
            self.current_pathname = None
            self.progress_bar.setMaximum(0)
            self.progress_bar.setValue(0)
            self.statusbar.update_left('Waiting for files...')
            return

        self.current_pathname = path

        print 'QUEUE PROCESSING:', path
        self.statusbar.update_left(path[len(self.current_watch_path):])
        self.abbyy_ocr.ocr(path)

    def closeEvent(self, event):
        self.file_queue.clear()  # Ensure the queue is clear for a clean exit.
        super(MainWindow, self).closeEvent(event)

    def path_received(self, path):
        self.abbyy_ocr.kill()
        path = str(path)
        print 'Path received:', path

        # Calculate output path and store it for when the file is done.
        if not self.current_pathname.endswith('.pdf'):
            out_path = '{0:s}.pdf'.format(self.current_pathname[:-4])
        else:
            # TODO: Add handler for input file being a PDF.
            out_path = '{0:s}.pdf'.format(self.current_pathname[:-4])

        try:
            move(path, out_path)
        except(IOError, OSError):
            print 'Error moving', path, 'to', out_path

        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.increment_processed()
        self.app.processEvents()  # Keep the GUI responsive during processing.
        self.process_next()

    def error_received(self, error_message):
        self.log('Error processing {0:s}:'.format(self.current_pathname), bold=True, colour='red')
        self.log('Error phrase matched: <b>{0:s}</b>'.format(error_message), indent=True)
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.increment_processed()
        self.app.processEvents()  # Keep the GUI responsive during processing.
        self.process_next()

    def reset(self):
        self.acrobat_proxy_listener.stop()
        self.progress_bar.setVisible(False)
        self.button_start.setChecked(False)
        self.file_queue = deque()
        self.queue_size_changed(0)

    @pyqtSignature('')
    def on_button_start_released(self):
        button_checked = self.button_start.isChecked()
        if not button_checked:
            return

        watch_folder = str(self.le_watch_folder.text())
        print watch_folder
        if not os.path.isdir(watch_folder):
            message_box_error(
                'Invalid watch folder',
                'Please set the watch folder to a valid path and try again.'
            )
            return

        # Set profile.
        if self.cb_profile.currentIndex():
            self.abbyy_ocr.current_profile = str(self.cb_profile.itemData(self.cb_profile.currentIndex()).toString())
        else:
            self.abbyy_ocr.current_profile = None
        print 'Current profile:', self.abbyy_ocr.current_profile

        self.current_watch_path = watch_folder
        self.log('Searching for files in <b>{0:s}</b>...'.format(watch_folder), status_bar=True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Get extension from radio buttons.
        if self.rb_tiff.isChecked():
            extension = ('.tiff', '.tif')
        elif self.rb_pdf.isChecked():
            extension = '.pdf'
        elif self.rb_jpeg.isChecked():
            extension = '.jpg'
        else:
            raise Exception('No extension selected')

        if not self.acrobat_proxy_listener.start():
            message_box_error('Error starting Acrobat Proxy Listener',
                              self.acrobat_proxy_listener.errorString())
            self.log('Error starting Acrobat Proxy Listener', colour='red')
            self.log(str(self.acrobat_proxy_listener.errorString()), indent=True, bold=True)
            self.reset()
            return

        self.file_watcher = FileWatcher(watch_folder, extension)
        self.file_watcher.count_change.connect(self.queue_size_changed)
        self.file_watcher.first_queue.connect(self.queue_received)
        self.file_watcher.queue_change.connect(self.watch_folder_changed)
        self.file_watcher.start()

    @pyqtSignature('')
    def on_tb_refresh_profiles_released(self):
        if hasattr(sys, 'frozen'):
            profiles_dir = os.path.join(os.path.dirname(sys.executable), 'profiles')
        else:
            profiles_dir = os.path.join(os.getcwd(), 'profiles')

        profiles_list = sorted(iglob('{0:s}/*.fbt'.format(profiles_dir)))

        self.cb_profile.clear()
        self.cb_profile.addItem('Last used ABBYY settings')
        for path in profiles_list:
            title = os.path.basename(path)[:-4]
            self.cb_profile.addItem(title, path)


