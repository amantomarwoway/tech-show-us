"""
src/media/license_checker.py - Verify asset licenses
"""

from urllib.parse import urlparse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Known free license sources
FREE_SOURCES = {
    'pexels.com': {'license': 'Pexels License', 'commercial': True, 'attribution': False},
    'pixabay.com': {'license': 'Pixabay License', 'commercial': True, 'attribution': False},
    'unsplash.com': {'license': 'Unsplash License', 'commercial': True, 'attribution': False},
    'giphy.com': {'license': 'Giphy License', 'commercial': True, 'attribution': False},
    'wikimedia.org': {'license': 'CC BY-SA', 'commercial': True, 'attribution': True},
    'nasa.gov': {'license': 'Public Domain', 'commercial': True, 'attribution': False},
    'whitehouse.gov': {'license': 'Public Domain', 'commercial': True, 'attribution': False}
}


def check_license(asset_url):
    """
    Check if asset license is safe for commercial use
    
    Returns:
        dict with license info and status
    """
    result = {
        'url': asset_url,
        'license': 'Unknown',
        'commercial_use_allowed': False,
        'modification_allowed': False,
        'attribution_required': True,
        'status': 'unknown'
    }
    
    if not asset_url:
        return result
    
    try:
        domain = urlparse(asset_url).netloc.lower().replace('www.', '')
        
        for source_domain, info in FREE_SOURCES.items():
            if source_domain in domain:
                result.update(info)
                result['status'] = 'verified'
                result['license'] = info['license']
                break
        
        # Check for .gov (public domain)
        if '.gov' in domain and result['status'] == 'unknown':
            result.update({
                'license': 'Public Domain (US Government)',
                'commercial_use_allowed': True,
                'modification_allowed': True,
                'attribution_required': False,
                'status': 'verified'
            })
    
    except Exception as e:
        logger.warning(f"License check failed for {asset_url}: {e}")
    
    return result


def verify_asset_safe(asset_url):
    """Quick check if asset is safe to use"""
    license_info = check_license(asset_url)
    
    if license_info['status'] != 'verified':
        logger.warning(f"Unverified license: {asset_url}")
        return False
    
    if not license_info['commercial_use_allowed']:
        logger.warning(f"Commercial use not allowed: {asset_url}")
        return False
    
    return True
