import glob
import os
import stat
import subprocess
import re
import tempfile
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QCoreApplication, QTimer
from PyQt4.QtNetwork import QLocalServer, QLocalSocket
from itertools import chain
from shutil import rmtree
import time
import pywinauto
from ui.custom_widgets import find_app_path

__author__ = 'Gary Hughes'

regex_pid = re.compile(r'(?<=^PID:\s)\d+$')


def get_abbyy_temp_folder(pid):
    base_folder = os.path.join(tempfile.gettempdir(), 'FineReader10')
    for folder_base in reversed(glob.glob('{0:s}/Untitled.FR10*'.format(base_folder))):
        for loc_file_path in glob.glob('{0:s}/{{*}}.loc'.format(folder_base)):
            with open(loc_file_path, 'r') as loc_file:
                for line in loc_file:
                    match = regex_pid.findall(line)
                    if len(match) == 1 and match[0] == str(pid):
                        return folder_base
    return None


class AppWatcher(QObject):
    # Signals
    error = pyqtSignal(str)

    check_phrases = (
        'Some licenses cannot be used',
        'Some of the pages have not been',
        'Process failed'
    )

    def __init__(self, proc, parent=None):
        super(AppWatcher, self).__init__(parent)
        self.proc = proc
        self.pid = proc.pid
        self.polls_without_dialog = 0
        self.current_temp_path = None
        print 'PID:', self.pid

    def start(self):
        print 'Starting watcher'
        self.abbyy_app = pywinauto.Application.connect(process=self.pid)
        """@type : Application"""
        self.abbyy_dialog = self.abbyy_app.window_(class_name='#32770')

        print QThread.currentThread()
        self.polling_timer = QTimer()
        self.polling_timer.setInterval(500)
        self.polling_timer.timeout.connect(self.poll)
        self.polling_timer.start()

    def poll(self):
        if not self.current_temp_path:
            self.current_temp_path = get_abbyy_temp_folder(self.pid)
            print 'Temp path set to', self.current_temp_path
        if not self.proc.poll() is None:
            # Application seems to have exited.
            print 'Abbyy quit?'
            self.error.emit('Abbyy exited before being able to process the file.')
            return
        if self.abbyy_dialog.Exists():
            # We have a dialog. Read it!
            static_texts = ''
            try:  # Wrap in a try block in case the pesky window vanishes while we're reading...
                try:
                    static_texts = ' '.join([
                        ' '.join(self.abbyy_dialog.Static.Texts()),
                        ' '.join(self.abbyy_dialog.Static2.Texts())
                    ]).strip()
                except MemoryError:
                    print 'Memory error when attempting to read text'
                except pywinauto.findwindows.WindowAmbiguousError:
                    # More than one dialog.
                    try:
                        static_texts = ' '.join(' '.join(c.Texts()) for c in chain.from_iterable(
                            x.Children() for x in self.abbyy_app.windows_(class_name='#32770')))
                    except MemoryError:
                        print 'Memory error when attempting to read text'
                        static_texts = ''
                if static_texts:
                    for phrase in self.check_phrases:
                        if phrase in static_texts:
                            self.error.emit(phrase)
                            self.abbyy_app.kill_()
                            break
            except pywinauto.findwindows.WindowNotFoundError:
                print 'Window went away. No biggy.'
                return
        else:
            self.polls_without_dialog += 1
            print '{0:.1f} seconds without activity...'.format(
                (self.polls_without_dialog * self.polling_timer.interval()) / 1000.0)
            if self.polls_without_dialog >= 20:
                # Abbyy is running but it doesn't look like it's doing anything. Kill it.
                self.error.emit('Abbyy was idle for too long without a dialog.')
                self.abbyy_app.kill_()
                return


class AbbyyOcr(QObject):
    # Signals
    error = pyqtSignal(str)

    def __init__(self, abbyy_path, parent=None):
        super(AbbyyOcr, self).__init__(parent)

        self.abbyy_path = abbyy_path
        self.app_watcher = None
        self.proc = None
        self.current_profile = None

    def ocr(self, path):
        options = ['/OptionsFile', self.current_profile] if self.current_profile else []
        args = [self.abbyy_path, path] + options + ['/send', 'Acrobat']

        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.proc = subprocess.Popen(args, startupinfo=startup_info)

        self.app_watcher_thread = QThread()

        self.app_watcher = AppWatcher(self.proc)
        self.app_watcher.moveToThread(self.app_watcher_thread)
        self.app_watcher.error.connect(self.emit_error)

        self.app_watcher_thread.started.connect(self.app_watcher.start)
        self.app_watcher_thread.finished.connect(self.app_watcher_thread.deleteLater)
        self.app_watcher_thread.start()

    def kill(self):
        print 'Killing...'
        try:
            abbyy_temp_path = self.app_watcher.current_temp_path
            if not abbyy_temp_path:
                abbyy_temp_path = get_abbyy_temp_folder(self.pid)
            self.proc.kill()
            self.proc.wait()
            self.proc = None
        except AttributeError:
            # The process has already been deleted.
            abbyy_temp_path = None

        try:
            self.app_watcher.deleteLater()
            self.app_watcher_thread.quit()
            self.app_watcher_thread.wait()
        except (RuntimeError, AttributeError):
            # self.app_watcher already deleted.
            pass

        # Try to remove temp files.
        if abbyy_temp_path:
            print 'Removing', abbyy_temp_path
            os.chmod(abbyy_temp_path, stat.S_IWRITE)
            try:
                rmtree(abbyy_temp_path)
                map(os.remove, glob.glob('{0:s}/*.tmp'.format(os.path.join(tempfile.gettempdir(), 'FineReader10'))))
            except (OSError, IOError, WindowsError):
                pass
        print 'Killed'

    def emit_error(self, error_message):
        self.kill()
        self.error.emit(error_message)


class AcrobatProxyListener(QLocalServer):
    # Signals
    new_path = pyqtSignal(str)

    def __init__(self, parent=None):
        super(AcrobatProxyListener, self).__init__(parent)
        self.newConnection.connect(self.on_new_connection)
        self.local_socket = QLocalSocket()

    def start(self):
        success = self.listen('Acrobat-Proxy-Listener')
        print 'Listening for Acrobat paths...'
        return success

    def stop(self):
        success = self.close()
        print 'Stopped listening for Acrobat paths'
        return success

    def on_new_connection(self):
        print 'NEW CONNECTION'
        self.local_socket = self.nextPendingConnection()
        self.local_socket.readyRead.connect(self.on_ready_read)

    def on_ready_read(self):
        print 'READING...'
        data = str(self.local_socket.readAll())
        self.local_socket.close()
        self.local_socket.deleteLater()
        print 'New path:', data
        self.new_path.emit(data)
