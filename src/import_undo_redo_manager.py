from collections import deque

class ImportUndoRedoManager:
    def __init__(self, firestore_service):
        self.firestore_service = firestore_service
        self.undo_stack = deque()
        self.redo_stack = deque()

    def record_action(self, action, collection, company_id, old_data, new_data):
        self.undo_stack.append((action, collection, company_id, old_data, new_data))
        self.redo_stack.clear()  # Clear redo stack when a new action is performed

    def undo(self):
        if not self.undo_stack:
            return False

        action, collection, company_id, old_data, new_data = self.undo_stack.pop()
        if action == 'add':
            self.firestore_service.delete_company(collection, company_id)
        elif action == 'update':
            self.firestore_service.update_company(collection, company_id, old_data)

        self.redo_stack.append((action, collection, company_id, old_data, new_data))
        return True

    def redo(self):
        if not self.redo_stack:
            return False

        action, collection, company_id, old_data, new_data = self.redo_stack.pop()
        if action == 'add':
            self.firestore_service.add_company(collection, new_data)
        elif action == 'update':
            self.firestore_service.update_company(collection, company_id, new_data)

        self.undo_stack.append((action, collection, company_id, old_data, new_data))
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0