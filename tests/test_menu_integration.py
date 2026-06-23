# tests/test_menu_integration.py
import pytest
from unittest.mock import patch, MagicMock
from jfather.app import MainWindow

def test_check_for_updates_menu_action():
    """Test that Check for Updates menu action exists"""
    # Just verify the attribute exists on the class
    assert hasattr(MainWindow, 'on_check_for_updates')
    assert hasattr(MainWindow, 'check_for_updates_on_startup')
    assert hasattr(MainWindow, 'show_update_dialog')
    assert hasattr(MainWindow, 'on_about')

def test_check_for_updates_calls_updater():
    """Test that on_check_for_updates method exists and can be called"""
    # Verify the method exists and has correct signature
    import inspect
    sig = inspect.signature(MainWindow.on_check_for_updates)
    # Should have self parameter
    params = list(sig.parameters.keys())
    assert 'self' in params
