import os
import platform
import win32file

from PyQt4.QtCore import QObject, pyqtSignal, QThread, Qt, QSettings, QMutex, QMutexLocker
from PyQt4.QtGui import QApplication, QLineEdit, QStatusBar, QLabel, QFrame
import win32api
import pywintypes
import win32con


__author__ = 'Gary Hughes'


def find_app_path(app_name):
    settings = QSettings('HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\'
                         'Windows\\CurrentVersion\\App Paths\\{0:s}.exe'.format(app_name),
                         QSettings.NativeFormat)
    return str(settings.value('Default', '').toString())


def get_exe_version(exe_path):
    try:
        info = win32api.GetFileVersionInfo(exe_path, '\\')
        version = map(int, (win32api.HIWORD(info['FileVersionMS']), win32api.LOWORD(info['FileVersionMS'])))
    except pywintypes.error:
        version = None
    return version


class FileWatcher(QObject):

    ACTIONS = {
        1: 'Created',
        2: 'Deleted',
        3: 'Updated',
        4: 'Renamed from something',
        5: 'Renamed to something'
    }

    FILE_LIST_DIRECTORY = 0x0001

    # Signals
    first_queue = pyqtSignal(list)
    queue_change = pyqtSignal(tuple)
    count_change = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, watch_folder, extension, parent=None):
        super(FileWatcher, self).__init__(parent)
        self.watch_folder = watch_folder
        self.extension = extension
        self.mutex = QMutex()
        self.stopping_value = False

    @property
    def stopping(self):
        mutex_locker = QMutexLocker(self.mutex)
        return self.stopping_value

    @stopping.setter
    def stopping(self, value):
        mutex_locker = QMutexLocker(self.mutex)
        self.stopping_value = value

    def start(self):
        # Build an initial queue.
        file_queue = []
        for dirpath, dirnames, filenames in os.walk(self.watch_folder):
            file_queue += [os.path.normpath(os.path.join(dirpath, x)) for x in filenames if
                           x.lower().endswith(self.extension)]
            self.count_change.emit(len(file_queue))

        self.first_queue.emit(file_queue)

        h_dir = win32file.CreateFile(
            self.watch_folder,
            self.FILE_LIST_DIRECTORY,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_FLAG_BACKUP_SEMANTICS,
            None
        )

        if self.stopping:
            self.finished.emit()
            return

        print 'Thread: Entering loop'

        while 1:
            results = win32file.ReadDirectoryChangesW(
                h_dir,
                10240,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_SIZE |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY,
                None,
                None
            )
            if self.stopping:
                self.finished.emit()
                return
            for action, filename in results:
                full_filename = os.path.normpath(os.path.join(self.watch_folder, filename))
                if not filename.lower().endswith(self.extension):
                    continue
                print (full_filename, self.ACTIONS.get(action, 'Unknown'))
                self.queue_change.emit((action, full_filename))

        print 'Watcher thread closing...'
        self.finished.emit()


class Win7Taskbar(QObject):
    TBPF_NOPROGRESS = 0
    TBPF_INDETERMINATE = 0x1
    TBPF_NORMAL = 0x2
    TBPF_ERROR = 0x4
    TBPF_PAUSED = 0x8

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.parent_window = parent
        if not (platform.system() == 'Windows' and platform.release() in ['7', 'post2008Server']):
            self.valid = False
            return

        tlb_path = os.path.join(QApplication.instance().utils_path, 'TaskbarLib.tlb')
        if not os.path.isfile(tlb_path):
            self.valid = False
            return

        import comtypes.client as cc

        cc.GetModule(tlb_path)
        import comtypes.gen.TaskbarLib as tbl

        self.taskbar = cc.CreateObject('{56FDF344-FD6D-11d0-958A-006097C9A090}', interface=tbl.ITaskbarList3)
        self.taskbar.HrInit()
        self.hWnd = parent.winId()
        self.valid = True

    def set_progress_value(self, value, total=100):
        if not self.valid:
            return
        self.taskbar.SetProgressValue(self.hWnd, value, total)

    def set_progress_state(self, state):
        if not self.valid:
            return
        self.taskbar.SetProgressState(self.hWnd, state)


class LineEdit_DragDrop_Folder(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) != 1:
                event.ignore()
                return
            path = str(urls[0].toLocalFile())
            if os.path.isdir(path):
                event.accept()
        elif event.mimeData().hasText():
            text = str(event.mimeData().text())
            if os.path.isdir(text):
                event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) != 1:
                event.ignore()
                return
            path = str(urls[0].toLocalFile())
            if os.path.isdir(path):
                self.setText(os.path.normpath(path))
                event.accept()
        elif event.mimeData().hasText():
            text = str(event.mimeData().text())
            if os.path.isdir(text):
                self.setText(os.path.normpath(text))
                event.accept()
        else:
            event.ignore()


class StatusBarLabel(QLabel):
    """ Custom QLabel for use in a QStatusBar object """

    def __init__(self, parent=None):
        """Constructor for StatusBarLabel"""
        super(StatusBarLabel, self).__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

    def setText(self, text):
        super(StatusBarLabel, self).setText(text)
        self.setToolTip(text)


class StatusBar(QStatusBar):

    def __init__(self, parent=None):
        super(StatusBar, self).__init__(parent)

        self.left_label = StatusBarLabel()
        self.middle_label = StatusBarLabel()
        self.right_label = StatusBarLabel()

        self.right_label.setAlignment(Qt.AlignRight)
        self.middle_label.setAlignment(Qt.AlignHCenter)

        self.addPermanentWidget(self.left_label, 2)
        self.addPermanentWidget(self.middle_label, 2)
        self.addPermanentWidget(self.right_label, 1)

        self.messageChanged.connect(self.update_left)

    def update_left(self, text):
        self.left_label.setText(text)

    def update_middle(self, text):
        self.middle_label.setText(text)

    def update_right(self, text):
        self.right_label.setText(text)

