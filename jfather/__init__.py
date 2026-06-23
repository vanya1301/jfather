"""jfather: desktop viewer/editor for large JSON."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("jfather")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback for development

__version_info__ = tuple(map(int, __version__.split(".")[:3]))
