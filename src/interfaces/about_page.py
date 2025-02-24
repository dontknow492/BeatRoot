import sys

import yaml
from loguru import logger

sys.path.append(r"D:\Program\Musify")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QUrl
from qfluentwidgets import ImageLabel, TitleLabel, SubtitleLabel, HyperlinkLabel

from src.common.myScroll import VerticalScrollWidget
from src.common.myFrame import VerticalFrame,  HorizontalFrame


def load_yaml():
    with open(r'D:\Program\Musify\app-info.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


class AboutPage(VerticalScrollWidget):
    def __init__(self, parent=None):
        super().__init__(title="About", parent=parent)
        self.setObjectName("AboutPage")
        self.app_info = load_yaml()
        logger.info(self.app_info)
        self.init_ui()

    def init_ui(self):
        logo = ImageLabel(self.app_info.get('icon'), self)
        tag_line = TitleLabel(self.app_info.get('tagline', "BeatRoot"), self)

        info_container = VerticalFrame(self)
        info_container.setLayoutMargins(0, 0, 0, 0)
        info_container.setContentSpacing(0)
        info_elements = ['Author', 'Version', 'Build', 'Channel', 'License']
        max_tag_width = 130
        for element in info_elements:
            container = HorizontalFrame(info_container)
            tag = self._create_tag(element)
            max_tag_width = max(max_tag_width, tag.sizeHint().width())
            tag.setMinimumWidth(max_tag_width)
            body = self._create_body(self.app_info.get(element.lower(), 'Unknown'))
            container.addWidget(tag)
            container.addWidget(body, stretch=1)
            info_container.addWidget(container)

        link_elements = ['Source', 'Bug Report', 'License']
        for element in link_elements:
            container = HorizontalFrame(info_container)
            tag = self._create_tag(element)
            max_tag_width = max(max_tag_width, tag.sizeHint().width())
            tag.setMinimumWidth(max_tag_width)
            element = element.replace(" ", "_")
            logger.debug(f"Element: {element}")
            body = self._create_link(self.app_info.get(element.lower(), 'Unknown'))
            container.addWidget(tag)
            container.addWidget(body, stretch=1)
            info_container.addWidget(container)
        # info_container.setMinimumWidth(600)

        self.addWidget(logo,  alignment=Qt.AlignmentFlag.AlignHCenter)
        self.addWidget(tag_line, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.addWidget(info_container,  alignment=Qt.AlignmentFlag.AlignHCenter)

    def _create_tag(self, text: str):
        if not text.endswith(' :'):
            text += ' :'
        tag = SubtitleLabel(text, self)
        tag.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return tag

    def _create_body(self, text: str):
        body = SubtitleLabel(text, self)
        body.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return body

    def _create_link(self,link: str, text: str = None):
        url = QUrl(link)
        if text is None:
            text = link.rsplit('/', maxsplit=1)[-1]
            text = text.capitalize()
            logger.debug(f"Text: {text}")
        body = HyperlinkLabel(url, text, self)
        body.setUnderlineVisible(True)
        return body


if __name__ == "__main__":
    app = QApplication([])
    about_page = AboutPage()
    about_page.show()
    app.exec()
