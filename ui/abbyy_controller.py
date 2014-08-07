import os
import subprocess
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QCoreApplication, QTimer
from PyQt4.QtNetwork import QLocalServer, QLocalSocket
from itertools import chain
import time
import pywinauto
from ui.custom_widgets import find_app_path

__author__ = 'Gary Hughes'


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
        if not self.proc.poll() is None:
            # Application seems to have exited.
            print 'Abbyy quit?'
            self.error.emit('Abbyy exited before being able to process the file.')
            return
        if self.abbyy_dialog.Exists():
            # We have a dialog. Read it!
            try:  # Wrap in a try block in case the pesky window vanishes while we're reading...
                try:
                    static_texts = ' '.join([
                        ' '.join(self.abbyy_dialog.Static.Texts()),
                        ' '.join(self.abbyy_dialog.Static2.Texts())
                    ]).strip()
                except pywinauto.findwindows.WindowAmbiguousError:
                    # More than one dialog.
                    static_texts = ' '.join(' '.join(c.Texts()) for c in chain.from_iterable(
                        x.Children() for x in self.abbyy_app.windows_(class_name='#32770')))
                    print 'STATIC TEXTS:', static_texts
                if static_texts:
                    for phrase in self.check_phrases:
                        if phrase in static_texts:
                            close_button = self.abbyy_dialog.CloseButton
                            while close_button.Exists():
                                print 'Click closed'
                                close_button.Click()
                                time.sleep(0.3)
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
            self.proc.kill()
            self.proc.wait()
            self.proc = None
        except AttributeError:
            # The process has already been deleted.
            pass

        try:
            self.app_watcher.deleteLater()
            self.app_watcher_thread.quit()
            self.app_watcher_thread.wait()
        except RuntimeError:
            # self.app_watcher already deleted.
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
