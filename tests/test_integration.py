# tests/test_integration.py
import pytest
from unittest.mock import patch, MagicMock
from jfather.updater import check_for_updates
from jfather.update_dialog import UpdateDialog
from PySide6.QtWidgets import QApplication

@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_full_update_flow(qapp):
    """Test complete update check and dialog flow"""
    release_info = {
        'tag_name': 'v0.2.0',
        'html_url': 'https://github.com/user/jfather/releases/tag/v0.2.0',
        'body': 'New features\n- Feature 1\n- Feature 2'
    }
    
    with patch('jfather.updater.get_latest_release') as mock_get:
        mock_get.return_value = release_info
        
        # Check for updates
        result = check_for_updates('0.1.0')
        assert result is not None
        assert result['tag_name'] == 'v0.2.0'
        
        # Create dialog
        dialog = UpdateDialog('0.1.0', result)
        assert dialog is not None
        assert dialog.windowTitle() == "Update Available"

def test_no_update_flow(qapp):
    """Test when no update available"""
    with patch('jfather.updater.get_latest_release') as mock_get:
        mock_get.return_value = {
            'tag_name': 'v0.1.0',
            'html_url': 'https://github.com/user/jfather/releases/tag/v0.1.0',
            'body': 'Initial release'
        }
        
        result = check_for_updates('0.1.0')
        assert result is None
