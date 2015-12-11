from collections import deque
from glob import iglob
import os
import re
from shutil import move
import shutil
import sys

from PyQt4.QtCore import pyqtSignature, QThread
from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog, QWidget

from ui.Ui_mainwindow import Ui_MainWindow
from ui.abbyy_controller import AcrobatProxyListener, AbbyyOcr
from ui.custom_widgets import Win7Taskbar, FileWatcher, find_app_path, get_exe_version
from ui.message_boxes import message_box_error
from ui.settings import Settings


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

        self.setWindowTitle('ABBYY Automator v{0:s}'.format(self.app.applicationVersion()))
        self.settings = Settings()

        self.get_app_paths()

        self.button_save_errors.setVisible(False)
        self.progress_bar.setVisible(0)
        self.on_tb_refresh_profiles_released()

        self.last_logged_text = ''

        self.file_watcher_threads = []
        self.file_watcher = None
        self.processed_count = 0
        self.skipped_count = 0
        self.file_queue = deque()
        self.current_pathname = None
        self.current_watch_path = None
        self.error_paths = []

        self.acrobat_proxy_listener = AcrobatProxyListener()
        self.acrobat_proxy_listener.new_path.connect(self.path_received)

        self.abbyy_ocr = AbbyyOcr(self.abby_path)
        self.abbyy_ocr.error.connect(self.error_received)

        self.update_processed_status()
        self.statusbar.update_left('Ready to begin')

        self.output_folder = ''

        self.load_settings()

    def save_settings(self):
        self.settings.last_watch_folder = self.le_watch_folder.text()
        self.settings.last_output_folder = self.le_output_folder.text()
        self.settings.last_profile = self.cb_profile.currentText()

    def load_settings(self):
        self.le_watch_folder.setText(self.settings.last_watch_folder)
        self.le_output_folder.setText(self.settings.last_output_folder)
        index = self.cb_profile.findText(self.settings.last_profile)
        if index == -1:
            self.cb_profile.setCurrentIndex(0)
        else:
            self.cb_profile.setCurrentIndex(index)

    def get_app_paths(self):
        # Get ABBYY path.
        self.abby_path = find_app_path('FineReader')
        if not self.abby_path or not os.path.isfile(self.abby_path):
            message_box_error('ABBYY FineReader not found',
                              'Could not find an ABBYY FineReader install on this machine.')
            sys.exit()

        # Check for version 10 of ABBYY.
        abbyy_dir = os.path.dirname(self.abby_path)
        if not abbyy_dir[-2:] == '10':
            ten_path = '{0:s}10\\FineReader.exe'.format(self.abby_path[-2:])
            if os.path.isfile(ten_path):
                self.abby_path = ten_path
            else:
                message_box_error('ABBYY FineReader 10 not found',
                                  'ABBYY FineReader was found on this machine, but a version other than 10.')
                sys.exit()

        # Get Acrobat path.
        self.acrobat_path = find_app_path('Acrobat')
        if not self.acrobat_path or not os.path.isfile(self.acrobat_path):
            message_box_error('Adobe Acrobat not found',
                              'Could not find an Adobe Acrobat install on this machine.')
            sys.exit()

    def install_acrobat_proxy(self):
        acrobat_backup_path = '{0:s}_.exe'.format(self.acrobat_path[:-4])
        acrobat_version = get_exe_version(self.acrobat_path)

        if acrobat_version[0] < 5 and os.path.isfile(acrobat_backup_path):
            # Proxy already installed.
            self.log('Acrobat proxy already installed.', bold=True)
            return True

        self.log('Installing Acrobat proxy over Acrobat v{0:d}.{1:d}...'.format(*acrobat_version), bold=True)
        try:
            # Backup existing Acrobat.exe.
            shutil.move(self.acrobat_path, acrobat_backup_path)
        except(OSError, IOError):
            self.log('Error moving Acrobat.exe - is Acrobat running?', bold=True, colour='red')
            return False

        try:
            # Copy Proxy in place of Acrobat
            shutil.copy('Acrobat Proxy.exe', self.acrobat_path)
        except(OSError, IOError):
            self.log('Error installing proxy - please check folder permissions.', bold=True, colour='red')
            return False

        return True

    def restore_acrobat(self):
        acrobat_backup_path = '{0:s}_.exe'.format(self.acrobat_path[:-4])
        acrobat_version = get_exe_version(acrobat_backup_path)
        proxy_version = get_exe_version(self.acrobat_path)

        if not acrobat_version and proxy_version:
            return False

        if proxy_version[0] > 5 and os.path.isfile(acrobat_backup_path):
            # Proxy not installed.
            self.log('Acrobat proxy not installed.', bold=True, colour='red')
            return True

        self.log('Restoring Acrobat v{0:d}.{1:d}...'.format(*acrobat_version), bold=True)
        try:
            # Backup existing Acrobat.exe.
            shutil.move(acrobat_backup_path, self.acrobat_path)
        except(OSError, IOError):
            self.log('Error moving Acrobat.exe - is Acrobat running?', bold=True, colour='red')
            return False

        return True

    def increment_processed(self):
        self.processed_count += 1
        self.update_processed_status()

    def update_processed_status(self):
        if not self.skipped_count:
            skipped_text = ''
        else:
            if self.skipped_count == 1:
                skipped_text = ' (1 file skipped)'
            else:
                skipped_text = ' ({0:,} files skipped)'.format(self.skipped_count)

        if self.processed_count == 1:
            self.statusbar.update_middle('1 file processed{0:s}'.format(skipped_text))
        else:
            self.statusbar.update_middle('{0:,} files processed{1:s}'.format(self.processed_count, skipped_text))

        queue_size = len(self.file_queue)
        if queue_size == 1:
            self.statusbar.update_right('1 file remaining')
        else:
            self.statusbar.update_right('{0:,} files remaining'.format(queue_size))

        self.app.processEvents()

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

    def queue_size_changed(self, count=None):
        # If we've items in the queue, we're in process mode and currently are not processing any files then start
        # on the next item in the queue.
        if not count:
            count = len(self.file_queue)
        if count and self.button_start.isChecked() and not self.current_pathname:
            print 'Processing restarted!'
            self.process_next()

    def queue_received(self, queue_list):
        print 'Received new queue'
        length = len(queue_list)
        self.file_queue = deque(queue_list)
        self.log('Found <b>{0:,} files'.format(length))

        self.progress_bar.setRange(0, length)
        self.update_processed_status()

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
        self.update_processed_status()
        self.queue_size_changed()
        self.adjust_progress_bars()

    def process_next(self):
        """
        Get next item in the queue and send it to ABBYY.
        """
        try:
            while True:
                # Keep pulling from the queue until the output file doesn't already exist.
                path = self.file_queue.popleft()
                out_path = os.path.join(self.output_folder,
                                        '{0:s}.pdf'.format(path[len(self.current_watch_path) + 1:-4]))
                print 'CHECKING', out_path
                if not os.path.isfile(out_path):
                    break
                self.skipped_count += 1
                self.update_processed_status()
        except IndexError:
            # Queue is empty.
            print 'QUEUE IS NOW EMPTY!'
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
        self.save_settings()
        self.file_queue.clear()  # Ensure the queue is clear for a clean exit.
        self.restore_acrobat()

        self.abbyy_ocr.kill()

        super(MainWindow, self).closeEvent(event)

    def path_received(self, path):
        self.abbyy_ocr.kill()
        path = str(path)
        print 'Path received:', path

        # Calculate output path and store it for when the file is done.
        out_path = os.path.join(self.output_folder,
                                '{0:s}.pdf'.format(self.current_pathname[len(self.current_watch_path) + 1:-4]))
        out_folder = os.path.dirname(out_path)
        if not os.path.isdir(out_folder):
            os.makedirs(out_folder)
        try:
            move(path, out_path)
        except(IOError, OSError):
            print 'Error moving', path, 'to', out_path

        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.increment_processed()
        self.update_processed_status()
        if self.button_start.isChecked():
            self.process_next()
        else:
            self.acrobat_proxy_listener.stop()

    def error_received(self, error_message):
        self.button_save_errors.setVisible(True)
        self.error_paths.append(self.current_pathname)
        self.log('Error processing {0:s}:'.format(self.current_pathname), bold=True, colour='red')
        self.log('Error phrase matched: <b>{0:s}</b>'.format(error_message), indent=True)
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.increment_processed()
        self.app.processEvents()  # Keep the GUI responsive during processing.
        self.process_next()

    def file_watcher_error(self, error_message):
        self.log('WATCH FOLDER ERROR:', colour='red', bold=True)
        self.log(error_message, indent=True, bold=True)
        message_box_error('Watch folder error', error_message)

        # Lock down all application controls other than the error log saving button.
        self.button_start.setChecked(False)
        for widget in (self.button_start, self.button_output_browse, self.button_watch_browse, self.cb_profile,
                       self.tb_refresh_profiles, self.rb_jpeg, self.rb_pdf, self.rb_tiff):
            widget.setEnabled(False)
        return

    def set_inputs_enabled(self, enabled=True):
        for item in (self.inputs_layout.itemAt(i).widget() for i in xrange(self.inputs_layout.count())):
            if isinstance(item, QWidget):
                item.setEnabled(enabled)

    def reset(self):
        self.acrobat_proxy_listener.stop()
        self.progress_bar.setVisible(False)
        self.button_start.setChecked(False)

        self.processed_count = 0
        self.skipped_count = 0
        self.file_queue = deque()
        self.update_processed_status()

    @pyqtSignature('')
    def on_button_reset_released(self):
        self.button_start.setChecked(False)

        print 'Stopping file watcher...'
        try:
            self.file_watcher.stopping = True
            self.file_watcher_thread.quit()
            # self.file_watcher_thread.terminate()

            del self.file_watcher
            # del self.file_watcher_thread
        except AttributeError:
            print 'Could not stop file watcher. Was it running?'
        print 'File watcher stopped.'

        self.reset()
        self.set_inputs_enabled(True)
        self.button_reset.setEnabled(False)

    @pyqtSignature('bool')
    def on_button_start_toggled(self, pressed):
        if not pressed:
            print 'Released!', pressed
            self.progress_bar.setVisible(False)
            self.statusbar.update_left('Ready to begin')
            if self.current_pathname is None:
                self.acrobat_proxy_listener.stop()
            return

        self.set_inputs_enabled(False)
        self.button_reset.setEnabled(True)

        self.output_folder = str(self.le_output_folder.text())
        print "Output folder:", self.output_folder

        watch_folder = str(self.le_watch_folder.text())
        print watch_folder
        if not os.path.isdir(watch_folder):
            message_box_error(
                'Invalid watch folder',
                'Please set the watch folder to a valid path and try again.'
            )
            self.button_start.setChecked(False)
            return

        # Set profile.
        if self.cb_profile.currentIndex():
            self.abbyy_ocr.current_profile = str(self.cb_profile.itemData(self.cb_profile.currentIndex()).toString())
        else:
            self.abbyy_ocr.current_profile = None
        print 'Current profile:', self.abbyy_ocr.current_profile

        print self.install_acrobat_proxy()
        # return

        self.current_watch_path = watch_folder
        self.log('Searching for files in <b>{0:s}</b>...'.format(watch_folder), status_bar=True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        if not self.acrobat_proxy_listener.start():
            message_box_error('Error starting Acrobat Proxy Listener',
                              self.acrobat_proxy_listener.errorString())
            self.log('Error starting Acrobat Proxy Listener', colour='red')
            self.log(str(self.acrobat_proxy_listener.errorString()), indent=True, bold=True)
            self.reset()
            return

        # if not hasattr(self, 'file_watcher_thread'):
            # Get extension from radio buttons.
        if self.rb_tiff.isChecked():
            extension = ('.tiff', '.tif')
        elif self.rb_pdf.isChecked():
            extension = '.pdf'
        elif self.rb_jpeg.isChecked():
            extension = '.jpg'
        else:
            raise Exception('No extension selected')

        self.file_watcher_thread = QThread()
        self.file_watcher_threads.append(self.file_watcher_thread)
        self.file_watcher = FileWatcher(watch_folder, extension)
        self.file_watcher.moveToThread(self.file_watcher_thread)
        self.file_watcher_thread.started.connect(self.file_watcher.start)
        self.file_watcher_thread.finished.connect(self.file_watcher_thread.deleteLater)
        self.file_watcher.finished.connect(self.file_watcher_thread.quit)
        self.file_watcher.count_change.connect(self.queue_size_changed)
        self.file_watcher.first_queue.connect(self.queue_received)
        self.file_watcher.queue_change.connect(self.watch_folder_changed)
        self.file_watcher.error.connect(self.file_watcher_error)

        if not self.file_watcher_thread.isRunning():
            self.file_watcher_thread.start()
        else:
            if self.file_queue:
                self.adjust_progress_bars()
                self.progress_bar.setValue(0)
                self.update_processed_status()
                self.process_next()

    @pyqtSignature('')
    def on_button_watch_browse_released(self):
        output_path = unicode(self.le_output_folder.text())
        if output_path and os.path.isdir(output_path):
            start_path = output_path
        else:
            start_path = None
        watch_path = QFileDialog.getExistingDirectory(self, 'Select an input folder', start_path)
        if not watch_path:
            return
        self.le_watch_folder.setText(watch_path)

    @pyqtSignature('')
    def on_button_output_browse_released(self):
        watch_path = unicode(self.le_watch_folder.text())
        if watch_path and os.path.isdir(watch_path):
            start_path = watch_path
        else:
            start_path = None
        output_path = QFileDialog.getExistingDirectory(self, 'Select an output folder', start_path)
        if not output_path:
            return
        self.le_output_folder.setText(output_path)

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

    @pyqtSignature('')
    def on_button_save_errors_released(self):
        error_log_path = QFileDialog.getSaveFileName(self, 'Save error log', filter='Text Files (*.txt)')
        if not error_log_path:
            return

        with open(error_log_path, 'w') as log_file:
            for item in self.error_paths:
                log_file.write('{0:s}\n'.format(item))


