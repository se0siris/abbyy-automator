import os
import re
import subprocess
import tempfile
from PyQt4.QtCore import QCoreApplication, QObject, pyqtSignal
from PyQt4.QtNetwork import QLocalSocket

from win32ui import MessageBox
import win32con

__author__ = 'Gary Hughes'


class AcrobatWriter(QLocalSocket):

    # Signals
    success = pyqtSignal()

    def __init__(self, parent=None):
        super(AcrobatWriter, self).__init__(parent)

    def write_path(self, path):
        self.connectToServer('Acrobat-Proxy-Listener')
        status = self.writeData(path)
        self.disconnectFromServer()
        if status:
            self.success.emit()
        return status


class Main(QObject):

    def __init__(self, passed_arguments, parent=None):
        super(Main, self).__init__(parent)
        self.app = QCoreApplication.instance()

        self.passed_arguments = passed_arguments

        # If there were no arguments just start Acrobat.
        if not passed_arguments:
            self.start_acrobat()
            return

        self.acrobat_writer = None
        self.pdf_path = passed_arguments[0]

        temp_dir = tempfile.gettempdir().replace('\\', '\\\\')
        match = re.match(r'^{}\\FineReader\d{{2}}\\tmp\w*\.pdf'.format(temp_dir), self.pdf_path, re.IGNORECASE)
        print r'{}\\FineReader\d{{2}}\\tmp\w{{4}}\.pdf$'.format(temp_dir)
        if match:
            # Path matched a FineReader temp path. Create an acrobat_writer object and send the path.
            self.send_abbyy_path()
            print "It's a match! :D"
        else:
            self.start_acrobat()
            print 'No match :('

        self.app_quit()

    def send_abbyy_path(self):
        self.acrobat_writer = AcrobatWriter()
        self.acrobat_writer.error.connect(self.error)
        self.acrobat_writer.success.connect(self.app_quit)
        self.acrobat_writer.write_path(self.passed_arguments[0])

    def start_acrobat(self):
        if hasattr(sys, 'frozen'):
            # Running as a packaged .exe. Acrobat will be in the current directory.
            acrobat_path = os.path.join(os.path.dirname(sys.executable), 'Acrobat_.exe')
        else:
            acrobat_path = r'C:\Program Files (x86)\Adobe\Acrobat 10.0\Acrobat\Acrobat.exe'

        if not os.path.isfile(acrobat_path):
            MessageBox('The Acrobat executable could not be found.',
                       'ABBYY Automator Acrobat Proxy',
                       win32con.MB_ICONERROR)
        else:
            subprocess.Popen([acrobat_path] + self.passed_arguments, close_fds=True)
        self.app_quit()

    def error(self, t):
        print 'There was an error!'
        if t == QLocalSocket.ServerNotFoundError:
            response = MessageBox(
                'An ABBYY path was detected, but the ABBYY Automator does not appear to be listening.\n\n'
                '{}\n\nOpen PDF in Acrobat?'.format(self.pdf_path),
                'ABBYY Automator Acrobat Proxy',
                win32con.MB_YESNO | win32con.MB_ICONQUESTION | win32con.MB_DEFBUTTON2
            )

            if response == win32con.IDYES:
                self.start_acrobat()

            print 'Server not found'
            self.app_quit()

    def app_quit(self):
        print 'All done'
        # with open('acrobat_proxy.log', 'w') as log_file:
        #     log_file.write(str(self.passed_arguments))
        self.app.quit()
        sys.exit()


if __name__ == "__main__":
    import sys

    app = QCoreApplication([sys.argv])
    main = Main(sys.argv[1:])