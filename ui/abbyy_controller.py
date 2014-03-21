import os
import subprocess
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QCoreApplication, QTimer
from PyQt4.QtNetwork import QLocalServer, QLocalSocket
import time
import pywinauto

__author__ = 'Gary Hughes'


class AppWatcher(QObject):

    # Signals
    error = pyqtSignal(str)

    check_phrases = (
        'The following errors occurred',
        'Some licenses cannot be used',
        'Some of the pages have not been',
        'Process failed'
    )

    def __init__(self, pid, parent=None):
        super(AppWatcher, self).__init__(parent)
        self.pid = pid

    def start(self):
        print 'Starting watcher'
        self.abbyy_app = pywinauto.Application.connect(process=self.pid)
        """@type : Application"""
        self.abbyy_dialog = self.abbyy_app.window_(class_name='#32770')

        print QThread.currentThread()
        self.test_timer = QTimer()
        self.test_timer.setInterval(500)
        self.test_timer.timeout.connect(self.poll)
        self.test_timer.start()

    def poll(self):
        if self.abbyy_dialog.Exists():
            # We have a dialog. Read it!
            try:  # Wrap in a try block in case the pesky window vanishes while we're reading...
                static_texts = ' '.join([
                    ' '.join(self.abbyy_dialog.Static.Texts()),
                    ' '.join(self.abbyy_dialog.Static2.Texts())
                ]).strip()
                if static_texts:
                    for phrase in self.check_phrases:
                        if phrase in static_texts:
                            close_button = self.abbyy_dialog.CloseButton
                            while close_button.Exists():
                                print 'Click closed'
                                close_button.Click()
                                time.sleep(0.3)
                            self.abbyy_app.kill_()
                            self.error.emit(phrase)
                            break
            except pywinauto.findwindows.WindowNotFoundError:
                print 'Window went away. No biggy.'
                return


class AbbyyOcr(QObject):

    # Signals
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super(AbbyyOcr, self).__init__(parent)

        self.app_watcher = None
        self.proc = None
        self.current_profile = None

        # TODO: Detect FineReader path on installed system instead of hard-coding.
        self.cmd = r'c:\Program Files (x86)\ABBYY FineReader 10\FineReader.exe'

    def ocr(self, path):
        options = ['/OptionsFile', self.current_profile] if self.current_profile else []
        args = [self.cmd, path] + options + ['/send', 'Acrobat']

        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.proc = subprocess.Popen(args, startupinfo=startup_info)
        pid = self.proc.pid
        print 'PID:', self.proc.pid

        self.app_watcher_thread = QThread()

        self.app_watcher = AppWatcher(pid)
        self.app_watcher.error.connect(self.emit_error)

        self.app_watcher_thread.started.connect(self.app_watcher.start)
        self.app_watcher_thread.finished.connect(self.app_watcher_thread.deleteLater)
        self.app_watcher.moveToThread(self.app_watcher_thread)
        self.app_watcher_thread.start()

    def kill(self):
        print 'Killing...'
        self.proc.kill()
        self.proc.wait()
        self.proc = None

        self.app_watcher.deleteLater()
        self.app_watcher_thread.quit()
        self.app_watcher_thread.wait()
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


if __name__ == "__main__":
    import sys
    app = QCoreApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())