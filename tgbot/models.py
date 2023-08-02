class TChat:
    def __init__(self, t):
        self.id, self.active, self.last_updated = t


class TService:
    def __init__(self, t):
        self.id, self.id_chat, self.id_type, self.active, self.last_updated, self.optional_url = t