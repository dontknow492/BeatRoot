import sys

from PySide6.QtCore import QStandardPaths, Signal
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FolderListSettingCard, SwitchSettingCard, OptionsSettingCard, HyperlinkCard, \
    ComboBoxSettingCard, SettingCardGroup, PrimaryPushSettingCard
from qfluentwidgets import qconfig, FluentIcon



from config.config import cfg

from src.common.myScroll import VerticalScrollWidget


class SettingInterface(VerticalScrollWidget):
    aboutSignal  = Signal()
    def __init__(self, parent=None):
        super().__init__(title= "Settings", parent=parent)
        self.setObjectName("SettingInterface")
        qconfig.load("config/config.json", cfg)
        self.init_ui()

        
    def init_ui(self):
        appearance_group = SettingCardGroup("Interface", self)
        playback_group = SettingCardGroup("Playback", self)
        download_group = SettingCardGroup("Download", self)
        about_group = SettingCardGroup("About", self)
        theme_card = OptionsSettingCard(
            cfg.theme,
            FluentIcon.BRUSH,
            "Application Theme",
            "Adjust the appearance of your application",
            texts=["Light", "Dark", "Follow System Settings"],
            parent= appearance_group
        )
        
        startup_page_card = OptionsSettingCard(
            configItem=cfg.startupPage,
            icon = FluentIcon.HOME,
            title= "Startup Page",
            content="Choose the page that opens when the application starts",
            texts=["Home", "Search", "Local"],
            parent=appearance_group
        )
        appearance_group.addSettingCards([
            theme_card,
            startup_page_card
        ])
        
        equalizer_card = SwitchSettingCard(
            FluentIcon.MUSIC,
            "Enable Equalizer",
            "Enable the equalizer feature",
            cfg.enable_equilizer,
            parent=playback_group
        )
        endless_play_card = SwitchSettingCard(
            FluentIcon.SYNC,
            "Endless Play",
            "Enable endless play",
            cfg.endless_play,
            parent=playback_group
        )
        normalize_audio_card = SwitchSettingCard(
            FluentIcon.BOOK_SHELF,
            "Normalize Audio",
            "Normalize the audio",
            cfg.normalize_audio,
            parent=playback_group
        )
        
        playback_group.addSettingCards([
            equalizer_card,
            endless_play_card,
            normalize_audio_card
        ])
        
        download_folder_card = FolderListSettingCard(
            configItem=cfg.downloadFolder,
            title="Download Folder",
            content="Select the default download folder",
            directory=QStandardPaths.writableLocation(QStandardPaths.MusicLocation),
            parent=download_group
        )
        
        download_codec = ComboBoxSettingCard(
            configItem=cfg.download_codec,
            icon=FluentIcon.DOWNLOAD,
            title="Download Codec",
            content="Select the default download codec",
            texts=["M4A('recommended')", "MP3", "WAV", "OPUS"],
            parent=download_group
        )
        
        download_group.addSettingCards([
            download_folder_card,
            download_codec
        ])
        
        github_card = HyperlinkCard(
            "https://github.com/dontknow492/BeatRoot.git",
            "GitHub",
            FluentIcon.GITHUB,
            "Official Github Repo of BeatRoot",
            "Visit the GitHub repository",
            parent=about_group
        )
        
        check_update_card = SwitchSettingCard(
            FluentIcon.UPDATE,
            "Check Update",
            "Automatically check for updates",
            cfg.check_update,
            parent=about_group
        )
        about_button = PrimaryPushSettingCard(
                    "BeatRoot",
                    FluentIcon.INFO,
                    "About BeatRoot"
        )
        about_group.addSettingCards([
            github_card,
            check_update_card,
            about_button
        ])
        
        self.addWidgets([
            appearance_group,
            playback_group,
            download_group,
            about_group
        ])
        about_button.clicked.connect(self.aboutSignal.emit)
        cfg.save()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SettingInterface()
    w.aboutSignal.connect(lambda: print("about"))
    w.show()
    app.exec()