from qfluentwidgets import QConfig, OptionsConfigItem, ConfigItem, OptionsValidator, BoolValidator
from qfluentwidgets import qconfig, setTheme, Theme

def on_theme_changed(value):
    if value == "Auto":
        setTheme(Theme.AUTO)
    elif value == "Light":
        setTheme(Theme.LIGHT)
    elif value == "Dark":
        setTheme(Theme.DARK)


class MyConfig(QConfig):
    startupPage = OptionsConfigItem("Interface", "StartupPage", "Home", OptionsValidator(["Home", "Search", "Local"]), restart=True)
    theme = OptionsConfigItem("Interface", "ThemeMode", "Light", OptionsValidator(["Light", "Dark", "Auto"]), restart=True)
    theme.valueChanged.connect(on_theme_changed)

    downloadFolder = ConfigItem("Download", "DownloadFolder", ["downloads/"], restart=True)
    download_codec = OptionsConfigItem("Download", "DownloadCodec", "M4A('recommended')", OptionsValidator(["M4A('recommended')", "MP3", "WAV", "OPUS"]),restart=True)
    
    check_update = ConfigItem("About", "CheckUpdate", True, validator= BoolValidator(), restart=True)
    
    enable_equilizer = ConfigItem("Playback", "EnableEqualizer", True, validator= BoolValidator(), restart=True)
    endless_play = ConfigItem("Playback", "EndlessPlay", True, validator= BoolValidator(), restart=True)
    normalize_audio = ConfigItem("Playback", "NormalizeAudio", True, validator= BoolValidator(), restart=True)
    
cfg =  MyConfig()
qconfig.load('config/config.json', cfg)