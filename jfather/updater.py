# jfather/updater.py
import requests
import re
from typing import Optional, Dict, Any

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"


def get_latest_release(owner: str = "rianichev-i", repo: str = "jfather") -> Optional[Dict[str, Any]]:
    """Fetch latest release from GitHub API"""
    try:
        url = GITHUB_API.format(owner=owner, repo=repo)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        return None


def parse_version(tag: str) -> tuple:
    """Parse version tag to tuple for comparison"""
    # Remove 'v' prefix if present
    if tag.startswith('v'):
        tag = tag[1:]
    # Extract numeric parts
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', tag)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)


def check_for_updates(current_version: str, owner: str = "rianichev-i", repo: str = "jfather") -> Optional[Dict[str, Any]]:
    """Check if updates are available"""
    latest = get_latest_release(owner, repo)
    if not latest:
        return None
    
    latest_tag = latest.get('tag_name', '')
    latest_version = parse_version(latest_tag)
    current_ver = parse_version(current_version)
    
    if latest_version > current_ver:
        return latest
    return None