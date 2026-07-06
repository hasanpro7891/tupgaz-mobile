from collections import defaultdict

class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)

    def publish(self, event_type, data=None):
        if data is None:
            data = {}
        for callback in self._listeners.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                print(f"[EventBus] Hata [{event_type}]: {e}")

    def subscribe(self, event_type, callback):
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        self._listeners[event_type] = [
            cb for cb in self._listeners[event_type] if cb != callback
        ]

    def clear(self):
        self._listeners.clear()
