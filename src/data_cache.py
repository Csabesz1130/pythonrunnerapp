import json
from collections import OrderedDict

class DataCache:
    def __init__(self, max_size=1000):
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def clear(self):
        self.cache.clear()

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(list(self.cache.items()), f)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                items = json.load(f)
                self.cache = OrderedDict(items)
        except FileNotFoundError:
            pass