"""Qt table model for arrays of JSON objects."""

import json

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


def is_tabular(data):
    """True when data is a non-empty list whose items are >= half dicts."""
    if not isinstance(data, list) or not data:
        return False
    dict_count = sum(1 for item in data if isinstance(item, dict))
    return dict_count * 2 >= len(data)


def _cell_display(value):
    if isinstance(value, dict):
        n = len(value)
        return f"{{\u2026}} {n} key" + ("" if n == 1 else "s")
    if isinstance(value, list):
        n = len(value)
        return f"[\u2026] {n} item" + ("" if n == 1 else "s")
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _cell_tooltip(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return None


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
        if not index.isValid():
            return None
        item = self._rows[index.row()]
        if isinstance(item, dict):
            key = self._columns[index.column()]
            value = item[key] if key in item else None
            present = key in item
        else:
            value = item if index.column() == 0 else None
            present = index.column() == 0
        if role == Qt.DisplayRole:
            if not present:
                return ""
            return _cell_display(value)
        if role == Qt.ToolTipRole:
            if not present:
                return None
            return _cell_tooltip(value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
            return None
        return section
