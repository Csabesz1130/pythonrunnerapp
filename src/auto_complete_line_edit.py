# File: src/ui/auto_complete_line_edit.py

import logging
from PyQt6.QtWidgets import QLineEdit, QCompleter
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel

class AutoCompleteLineEdit(QLineEdit):
    """
    A QLineEdit with auto-completion functionality.
    """

    # Signal emitted when a completion is selected
    completion_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing AutoCompleteLineEdit")

        self._completion_items = []
        self._last_typed = ""

        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)

        self.textEdited.connect(self._on_text_edited)
        self.completer.activated.connect(self._on_completion_selected)

        self.logger.info("AutoCompleteLineEdit initialized")

    def set_completion_items(self, items):
        """
        Set the list of items to be used for auto-completion.

        :param items: List of strings to use for auto-completion
        """
        self.logger.info(f"Setting completion items. Count: {len(items)}")
        self._completion_items = items
        model = QStringListModel(self._completion_items)
        self.completer.setModel(model)

    def _on_text_edited(self, text):
        """
        Handle text editing in the line edit.

        :param text: Current text in the line edit
        """
        self.logger.debug(f"Text edited: {text}")
        if len(text) < len(self._last_typed):
            # Text was deleted, reset completer
            self.logger.debug("Text deleted, resetting completer")
            self.completer.setCompletionPrefix("")
        else:
            # Update completer
            self.logger.debug("Updating completer")
            self.completer.setCompletionPrefix(text)

        self._last_typed = text

        # Show all completions if the text is empty
        if not text:
            self.logger.debug("Showing all completions")
            self.completer.setCompletionPrefix("")
            self.completer.complete()

    def _on_completion_selected(self, text):
        """
        Handle selection of a completion item.

        :param text: Selected completion text
        """
        self.logger.info(f"Completion selected: {text}")
        self.setText(text)
        self.completion_selected.emit(text)

    def keyPressEvent(self, event):
        """
        Handle key press events.

        :param event: QKeyEvent
        """
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.logger.debug("Enter/Return key pressed")
            if self.completer.popup().isVisible():
                event.ignore()
                return

        super().keyPressEvent(event)

    def focusInEvent(self, event):
        """
        Handle focus in event.

        :param event: QFocusEvent
        """
        self.logger.debug("Focus in event")
        if not self.text():
            self.completer.setCompletionPrefix("")
            self.completer.complete()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """
        Handle focus out event.

        :param event: QFocusEvent
        """
        self.logger.debug("Focus out event")
        self.completer.popup().hide()
        super().focusOutEvent(event)

# Usage example:
# In your MainWindow or any other widget:
# self.search_input = AutoCompleteLineEdit()
# self.search_input.set_completion_items(["Item 1", "Item 2", "Item 3"])
# self.search_input.completion_selected.connect(self.on_search_completed)
# layout.addWidget(self.search_input)