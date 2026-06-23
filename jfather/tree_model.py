"""Lazy Qt tree model exposing a parsed JSON object."""

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt


def type_name(value):
    """Return the JSON type name for a Python value."""
    if isinstance(value, bool):
        return "boolean"
    if value is None:
        return "null"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


class JsonNode:
    """A node wrapping a key/value; children are built lazily."""

    def __init__(self, key, value, parent=None, row=0):
        self.key = key
        self.value = value
        self.parent = parent
        self.row = row
        self._children = None

    @property
    def is_container(self):
        return isinstance(self.value, (dict, list))

    def child_count(self):
        if isinstance(self.value, dict):
            return len(self.value)
        if isinstance(self.value, list):
            return len(self.value)
        return 0

    def children(self):
        if self._children is None:
            self._children = []
            if isinstance(self.value, dict):
                for row, (key, value) in enumerate(self.value.items()):
                    self._children.append(JsonNode(key, value, self, row))
            elif isinstance(self.value, list):
                for row, value in enumerate(self.value):
                    self._children.append(JsonNode(row, value, self, row))
        return self._children


def index_for_path(model, path):
    """Resolve a path (list of keys/indices) to its column-0 QModelIndex.

    Returns an invalid QModelIndex if any path segment cannot be found.
    """
    from PySide6.QtCore import QModelIndex

    parent = QModelIndex()
    for key in path:
        match = QModelIndex()
        for row in range(model.rowCount(parent)):
            candidate = model.index(row, 0, parent)
            if candidate.internalPointer().key == key:
                match = candidate
                break
        if not match.isValid():
            return QModelIndex()
        parent = match
    return parent


def _value_text(value):
    if isinstance(value, dict):
        return "{%d items}" % len(value)
    if isinstance(value, list):
        return "[%d items]" % len(value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class JsonTreeModel(QAbstractItemModel):
    """Read/display model over a parsed JSON object."""

    HEADERS = ["Key", "Value", "Type"]

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._root = JsonNode("root", data if data is not None else {})

    def set_json(self, data):
        self.beginResetModel()
        self._root = JsonNode("root", data if data is not None else {})
        self.endResetModel()

    def _node(self, index):
        if index.isValid():
            return index.internalPointer()
        return self._root

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        children = self._node(parent).children()
        if 0 <= row < len(children):
            return self.createIndex(row, column, children[row])
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        parent = index.internalPointer().parent
        if parent is None or parent is self._root:
            return QModelIndex()
        return self.createIndex(parent.row, 0, parent)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        return self._node(parent).child_count()

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def hasChildren(self, parent=QModelIndex()):
        return self._node(parent).child_count() > 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        node = index.internalPointer()
        column = index.column()
        if column == 0:
            return str(node.key)
        if column == 1:
            return _value_text(node.value)
        if column == 2:
            return type_name(node.value)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None
