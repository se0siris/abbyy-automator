import os
import sys
import traceback
from PyQt4.QtCore import QSharedMemory
from PyQt4.QtGui import QApplication, QStyleFactory, QIcon

import cStringIO as StringIO
import time
from ui.mainwindow import MainWindow
from ui.message_boxes import message_box_error

__author__ = 'Gary Hughes'


VERSION = '1.0.5 (21/08/2014)'


def except_hook(exc_type, exc_value, traceback_obj):
    """
    Global function to catch unhandled exceptions.
    """
    separator = '-' * 80
    log_file = "error.log"
    notice = '''An unhandled exception occurred. Please report the problem
                via email to <a href="mailto:support@pearl-scan.co.uk">support@pearl-scan.co.uk</a>.<br>
                A log has been written to "<i>error.log</i>" in your application folder.<br><br>
                Error information:\n'''
    time_string = time.strftime("%Y-%m-%d, %H:%M:%S")
    machine_name = os.getenv('COMPUTERNAME')
    user_name = os.getenv('USERNAME')

    tb_info_file = StringIO.StringIO()
    traceback.print_tb(traceback_obj, None, tb_info_file)
    tb_info_file.seek(0)
    tb_info = tb_info_file.read()
    error_message = '%s: \n%s' % (str(exc_type), str(exc_value))
    sections = [separator, time_string,
                'Username: {}'.format(user_name),
                'Machine: {}'.format(machine_name),
                'Version: {}'.format(VERSION),
                separator, error_message,
                separator, tb_info]
    msg = '\n'.join(sections)
    try:
        with open(log_file, 'w') as f:
            f.write(msg)
            f.write(VERSION)
    except IOError:
        pass
    message_box_error(notice, str(msg))


def instance_check(app):
    app.instance_check = QSharedMemory('Abbyy Automator - Shared Memory Check')
    if not app.instance_check.create(10):
        # Already running...
        return False
    return True


def start_main():
    app = QApplication(sys.argv)

    icon = QIcon(':/icons/application.png')
    app.setWindowIcon(icon)

    # If compiled as a one-file PyInstaller package look for Qt4 Plugins in the TEMP folder.
    try:
        extra_path = [os.path.join(sys._MEIPASS, 'qt4_plugins')]
        app.setLibraryPaths(app.libraryPaths() + extra_path)
        app.utils_path = os.path.join(sys._MEIPASS, 'utils')
    except AttributeError:
        app.utils_path = os.path.join(os.getcwd(), 'utils')

    # Error handling stuff.
    if hasattr(sys, 'frozen'):
        sys.excepthook = except_hook

    app.setApplicationName('ABBYY Automator')
    app.setApplicationVersion(VERSION)
    app.setOrganizationName('Pearl Scan Solutions')

    print 'AppName: %s' % app.applicationName()
    print 'AppVersion: %s' % app.applicationVersion()
    print 'Company Name: %s' % app.organizationName()

    app.setStyle(QStyleFactory.create('Cleanlooks'))
    app.setPalette(QApplication.style().standardPalette())

    if not instance_check(app):
        message_box_error('Program already running.',
                          'You can only have one copy of ABBYY Automator running at once.')
        sys.exit()

    mainwindow = MainWindow()
    mainwindow.show()
    app.exec_()
    app.closeAllWindows()
    app.quit()

if __name__ == "__main__":
    start_main()
    print 'Application closed'
    sys.exit()