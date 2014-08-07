import os
from PyQt4.QtCore import QSettings, QVariant, QString

__author__ = 'Gary Hughes'


class Settings(object):
    """
    Wrapper for the settings file to get/set values.
    """

    def __init__(self):
        settings_path = 'settings.ini'
        self.settings = QSettings(settings_path, QSettings.IniFormat)

    @property
    def last_watch_folder(self):
        last_folder = self.settings.value('last_settings/watch_folder', QVariant('')).toString()
        if os.path.isdir(str(last_folder)):
            return last_folder
        return QString()

    @last_watch_folder.setter
    def last_watch_folder(self, path):
        self.settings.setValue('last_settings/watch_folder', path)

    @property
    def last_output_folder(self):
        last_folder = self.settings.value('last_settings/output_folder', QVariant('')).toString()
        if os.path.isdir(str(last_folder)):
            return last_folder
        return QString()

    @last_output_folder.setter
    def last_output_folder(self, path):
        self.settings.setValue('last_settings/output_folder', path)

    @property
    def last_profile(self):
        return self.settings.value('last_settings/profile', QVariant('')).toString()

    @last_profile.setter
    def last_profile(self, path):
        self.settings.setValue('last_settings/profile', path)
