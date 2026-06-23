"""Qt table model for arrays of JSON objects."""

import json

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


def is_tabular(data):
    """True when data is a non-empty list whose items are >= half dicts."""
    if not isinstance(data, list) or not data:
        return False
    dict_count = sum(1 for item in data if isinstance(item, dict))
    return dict_count * 2 >= len(data)


def _cell_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class JsonTableModel(QAbstractTableModel):
    """Rows = objects; columns = union of their keys (first-seen order)."""

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = []
        self._columns = []
        if rows is not None:
            self.set_rows(rows)

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows)
        columns = []
        seen = set()
        for item in self._rows:
            if isinstance(item, dict):
                for key in item.keys():
                    if key not in seen:
                        seen.add(key)
                        columns.append(key)
        self._columns = columns
        self.endResetModel()

    def row_object(self, row):
        return self._rows[row]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = self._rows[index.row()]
        if isinstance(item, dict):
            key = self._columns[index.column()]
            if key in item:
                return _cell_text(item[key])
            return ""
        return _cell_text(item) if index.column() == 0 else ""

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
            return None
        return section
