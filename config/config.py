from qfluentwidgets import QConfig, OptionsConfigItem, ConfigItem, OptionsValidator, BoolValidator

class MyConfig(QConfig):
    startupPage = OptionsConfigItem("Interface", "StartupPage", "Home", OptionsValidator(["Home", "Search", "Local"]), restart=True)
    theme = OptionsConfigItem("Interface", "ThemeMode", "Auto", OptionsValidator(["Auto", "Light", "Dark"]), restart=True)
    
    downloadFolder = ConfigItem("Download", "DownloadFolder", [], restart=True)
    download_codec = OptionsConfigItem("Download", "DownloadCodec", "M4A('recommended')", OptionsValidator(["M4A('recommended')", "MP3", "WAV", "OPUS"]),restart=True)
    
    check_update = ConfigItem("About", "CheckUpdate", True, validator= BoolValidator(), restart=True)
    
    enable_equilizer = ConfigItem("Playback", "EnableEqualizer", True, validator= BoolValidator(), restart=True)
    endless_play = ConfigItem("Playback", "EndlessPlay", True, validator= BoolValidator(), restart=True)
    normalize_audio = ConfigItem("Playback", "NormalizeAudio", True, validator= BoolValidator(), restart=True)
    
if(__name__ == "__main__"):
    config = MyConfig()
    # config.themeMode = "Dark"
    # config.startupPage = "Search"
    # config.downloadFolder = "data\\downloads"
    print(config.themeMode)
    print(config.startupPage)
    print(config.downloadFolder)