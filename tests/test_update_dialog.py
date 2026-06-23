# tests/test_update_dialog.py
import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from jfather.update_dialog import UpdateDialog

@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_update_dialog_creation(qapp):
    release_info = {
        'tag_name': 'v0.2.0',
        'html_url': 'https://github.com/user/jfather/releases/tag/v0.2.0',
        'body': 'New features\n- Feature 1\n- Feature 2'
    }
    dialog = UpdateDialog('0.1.0', release_info)
    assert dialog is not None
    assert dialog.windowTitle() == "Update Available"

def test_update_dialog_no_update(qapp):
    dialog = UpdateDialog('0.1.0', None)
    assert dialog is not None

