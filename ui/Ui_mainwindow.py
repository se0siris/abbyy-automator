# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'S:\dev\Python\ABBYY Automator\ui\mainwindow.ui'
#
# Created: Fri Mar 21 14:19:08 2014
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(590, 432)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/application.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.fr_top_controls = QtGui.QFrame(self.centralwidget)
        self.fr_top_controls.setFrameShape(QtGui.QFrame.StyledPanel)
        self.fr_top_controls.setFrameShadow(QtGui.QFrame.Raised)
        self.fr_top_controls.setObjectName(_fromUtf8("fr_top_controls"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.fr_top_controls)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.button_browse = QtGui.QPushButton(self.fr_top_controls)
        self.button_browse.setObjectName(_fromUtf8("button_browse"))
        self.gridLayout.addWidget(self.button_browse, 0, 2, 1, 1)
        self.le_watch_folder = LineEdit_DragDrop_Folder(self.fr_top_controls)
        self.le_watch_folder.setObjectName(_fromUtf8("le_watch_folder"))
        self.gridLayout.addWidget(self.le_watch_folder, 0, 1, 1, 1)
        self.label = QtGui.QLabel(self.fr_top_controls)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.fr_top_controls)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.cb_profile = QtGui.QComboBox(self.fr_top_controls)
        self.cb_profile.setObjectName(_fromUtf8("cb_profile"))
        self.cb_profile.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cb_profile, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.fr_top_controls)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.frame = QtGui.QFrame(self.fr_top_controls)
        self.frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.frame)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.rb_tiff = QtGui.QRadioButton(self.frame)
        self.rb_tiff.setChecked(True)
        self.rb_tiff.setObjectName(_fromUtf8("rb_tiff"))
        self.horizontalLayout.addWidget(self.rb_tiff)
        self.rb_pdf = QtGui.QRadioButton(self.frame)
        self.rb_pdf.setObjectName(_fromUtf8("rb_pdf"))
        self.horizontalLayout.addWidget(self.rb_pdf)
        self.rb_jpeg = QtGui.QRadioButton(self.frame)
        self.rb_jpeg.setObjectName(_fromUtf8("rb_jpeg"))
        self.horizontalLayout.addWidget(self.rb_jpeg)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addWidget(self.frame, 2, 1, 1, 1)
        self.tb_refresh_profiles = QtGui.QToolButton(self.fr_top_controls)
        self.tb_refresh_profiles.setText(_fromUtf8(""))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/view-refresh.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tb_refresh_profiles.setIcon(icon1)
        self.tb_refresh_profiles.setIconSize(QtCore.QSize(16, 16))
        self.tb_refresh_profiles.setObjectName(_fromUtf8("tb_refresh_profiles"))
        self.gridLayout.addWidget(self.tb_refresh_profiles, 1, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.verticalLayout_3.addWidget(self.fr_top_controls)
        self.pte_log = QtGui.QPlainTextEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.pte_log.sizePolicy().hasHeightForWidth())
        self.pte_log.setSizePolicy(sizePolicy)
        self.pte_log.setReadOnly(True)
        self.pte_log.setPlainText(_fromUtf8(""))
        self.pte_log.setObjectName(_fromUtf8("pte_log"))
        self.verticalLayout_3.addWidget(self.pte_log)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.progress_bar = QtGui.QProgressBar(self.centralwidget)
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setObjectName(_fromUtf8("progress_bar"))
        self.horizontalLayout_2.addWidget(self.progress_bar)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.button_start = QtGui.QPushButton(self.centralwidget)
        self.button_start.setCheckable(True)
        self.button_start.setChecked(False)
        self.button_start.setObjectName(_fromUtf8("button_start"))
        self.horizontalLayout_2.addWidget(self.button_start)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = StatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.button_start, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.fr_top_controls.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "ABBYY Automator", None))
        self.button_browse.setText(_translate("MainWindow", "Browse", None))
        self.le_watch_folder.setText(_translate("MainWindow", "C:\\temp\\watching", None))
        self.label.setText(_translate("MainWindow", "Watch folder", None))
        self.label_2.setText(_translate("MainWindow", "Profile", None))
        self.cb_profile.setItemText(0, _translate("MainWindow", "Last used ABBYY settings", None))
        self.label_3.setText(_translate("MainWindow", "Filetype", None))
        self.rb_tiff.setText(_translate("MainWindow", "Tiff", None))
        self.rb_pdf.setText(_translate("MainWindow", "Pdf", None))
        self.rb_jpeg.setText(_translate("MainWindow", "Jpeg", None))
        self.tb_refresh_profiles.setToolTip(_translate("MainWindow", "Refresh profiles", None))
        self.button_start.setText(_translate("MainWindow", "Start", None))

from custom_widgets import StatusBar, LineEdit_DragDrop_Folder
import res_rc
