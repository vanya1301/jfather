# tests/test_updater.py
import pytest
from unittest.mock import patch, MagicMock
from jfather import updater


def test_check_for_updates_no_update():
    """Test when current version is latest"""
    with patch('jfather.updater.get_latest_release') as mock_get:
        mock_get.return_value = {
            'tag_name': 'v0.1.0',
            'html_url': 'https://github.com/user/jfather/releases/tag/v0.1.0',
            'body': 'Initial release'
        }
        result = updater.check_for_updates('0.1.0')
        assert result is None


def test_check_for_updates_has_update():
    """Test when newer version available"""
    with patch('jfather.updater.get_latest_release') as mock_get:
        mock_get.return_value = {
            'tag_name': 'v0.2.0',
            'html_url': 'https://github.com/user/jfather/releases/tag/v0.2.0',
            'body': 'New features\n- Feature 1\n- Feature 2'
        }
        result = updater.check_for_updates('0.1.0')
        assert result is not None
        assert result['tag_name'] == 'v0.2.0'
        assert '0.2.0' in result['html_url']


def test_version_parsing():
    """Test version comparison logic"""
    with patch('jfather.updater.get_latest_release') as mock_get:
        mock_get.return_value = {
            'tag_name': 'v1.10.0',
            'html_url': 'https://github.com/user/jfather/releases/tag/v1.10.0',
            'body': 'Major release'
        }
        # 1.10.0 > 1.2.0
        result = updater.check_for_updates('1.2.0')
        assert result is not None
        assert result['tag_name'] == 'v1.10.0'
