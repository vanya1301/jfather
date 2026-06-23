# tests/test_version.py
import jfather


def test_version_exists():
    assert hasattr(jfather, '__version__')
    assert isinstance(jfather.__version__, str)
    assert len(jfather.__version__) > 0


def test_version_info_exists():
    assert hasattr(jfather, '__version_info__')
    assert isinstance(jfather.__version_info__, tuple)
    assert len(jfather.__version_info__) >= 3
