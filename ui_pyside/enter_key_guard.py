from PySide6.QtCore import QObject, QEvent, Qt

class EnterToFinishFilter(QObject):
    """EventFilter for QLineEdit to consume Enter/Return and call a finish callback."""
    def __init__(self, finish_cb):
        super().__init__()
        self._finish_cb = finish_cb

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            try:
                if callable(self._finish_cb):
                    self._finish_cb()
            finally:
                return True  # consume event
        return False
