from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging

class FirestoreListener(QObject):
    data_changed = pyqtSignal(dict, str)  # Emits data and change_type

    def __init__(self, firestore_service, collection):
        super().__init__()
        self.firestore_service = firestore_service
        self.collection = collection
        self.listener = None
        self.batch_size = 50
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self.emit_batch)
        self.batch_timer.start(1000)  # Emit batch every second
        self.current_batch = []

    def start_listening(self):
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                try:
                    if change.type.name in ['ADDED', 'MODIFIED']:
                        self.data_changed.emit(change.document.to_dict(), change.type.name)
                    elif change.type.name == 'REMOVED':
                        self.data_changed.emit({'Id': change.document.id}, 'REMOVED')
                except Exception as e:
                    logging.error(f"Error processing Firestore change: {e}", exc_info=True)

        self.listener = self.firestore_service.db.collection(self.collection).on_snapshot(on_snapshot)

    def stop_listening(self):
        if self.listener:
            self.listener.unsubscribe()
        self.batch_timer.stop()

    def emit_batch(self):
        if self.current_batch:
            self.data_changed.emit(self.current_batch)
            self.current_batch = []

