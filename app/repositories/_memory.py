from dataclasses import replace


class MemoryTable:
    def __init__(self):
        self._rows = {}
        self._next_id = 1

    def add(self, entity):
        entity.id = self._next_id
        self._next_id += 1
        self._rows[entity.id] = replace(entity)
        return entity

    def get(self, entity_id):
        row = self._rows.get(entity_id)
        return replace(row) if row else None

    def save(self, entity):
        self._rows[entity.id] = replace(entity)
        return entity

    def delete(self, entity_id):
        self._rows.pop(entity_id, None)

    def all(self):
        return [replace(r) for _, r in sorted(self._rows.items())]
