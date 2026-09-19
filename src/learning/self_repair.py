"""
src/learning/self_repair.py - Self diagnostics and repair
"""

import os
import subprocess
from datetime import datetime, timedelta
from src.utils.logger import setup_logger
from src.database import get_connection
from src.learning.auto_optimizer import set_config, get_config

logger = setup_logger(__name__)


def run_self_diagnostics():
    """
    Check all components, repair if possible
    Returns: dict with status of each component
    """
    logger.info("=" * 60)
    logger.info("🔧 SELF-DIAGNOSTICS")
    logger.info("=" * 60)
    
    status = {
        "gemini": check_gemini(),
        "github_models": check_github_models(),
        "pexels": check_pexels(),
        "youtube": check_youtube(),
        "database": check_database(),
        "disk": check_disk(),
        "tts": check_tts(),
        "ffmpeg": check_ffmpeg(),
    }
    
    # Log status
    for name, ok in status.items():
        emoji = "✅" if ok else "❌"
        logger.info(f"   {emoji} {name}: {'OK' if ok else 'FAILED'}")
    
    # Try repairs
    failed = [k for k, v in status.items() if not v]
    if failed:
        logger.warning(f"⚠️ {len(failed)} components failed: {failed}")
        attempt_repairs(failed)
    
    return status


def check_gemini():
    """Check Gemini API"""
    try:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            return False
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="Say OK"
        )
        return bool(getattr(resp, 'text', ''))
    except:
        return False


def check_github_models():
    """Check GitHub Models"""
    try:
        token = os.getenv("GITHUB_TOKEN", "")
        if not token:
            return False
        from openai import OpenAI
        client = OpenAI(
            api_key=token,
            base_url="https://models.github.ai/inference"
        )
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10
        )
        return bool(resp.choices[0].message.content)
    except:
        return False


def check_pexels():
    """Check Pexels API"""
    try:
        key = os.getenv("PEXELS_API_KEY", "")
        if not key:
            return False
        import requests
        r = requests.get(
            "https://api.pexels.com/videos/search?query=test&per_page=1",
            headers={"Authorization": key},
            timeout=10
        )
        return r.status_code == 200
    except:
        return False


def check_youtube():
    """Check YouTube credentials"""
    try:
        cid = os.getenv("YT_CLIENT_ID", "")
        csec = os.getenv("YT_CLIENT_SECRET", "")
        rt = os.getenv("YT_REFRESH_TOKEN", "")
        return all([cid, csec, rt])
    except:
        return False


def check_database():
    """Check DB integrity"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stories")
        cursor.fetchone()
        conn.close()
        return True
    except:
        return False


def check_disk():
    """Check disk space"""
    try:
        stat = os.statvfs('/')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        logger.info(f"   💾 Free disk: {free_gb:.1f} GB")
        return free_gb > 1
    except:
        return True


def check_tts():
    """Check Piper TTS"""
    try:
        import piper
        return True
    except:
        return False


def check_ffmpeg():
    """Check FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def attempt_repairs(failed_components):
    """Attempt automatic repairs"""
    logger.info("=" * 60)
    logger.info("🔨 ATTEMPTING REPAIRS")
    logger.info("=" * 60)
    
    for component in failed_components:
        if component == "database":
            repair_database()
        elif component == "disk":
            clean_old_files()
        elif component == "ffmpeg":
            logger.warning("   FFmpeg repair requires system-level access")
        elif component in ["gemini", "github_models"]:
            logger.info(f"   {component} is temporary - will retry next run")


def repair_database():
    """Rebuild database if corrupted"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        logger.info("   ✅ Database repaired (VACUUM)")
    except Exception as e:
        logger.error(f"   Database repair failed: {e}")


def clean_old_files():
    """Clean old temp files"""
    try:
        from src.config import PATHS
        import glob
        
        # Clean old temp files (>1 day)
        cutoff = datetime.now() - timedelta(days=1)
        
        for pattern in [os.path.join(PATHS['temp'], '*'),
                        os.path.join(PATHS['output_videos'], '*.mp4')]:
            for file in glob.glob(pattern):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file))
                    if mtime < cutoff and 'short_' in file:
                        os.remove(file)
                        logger.info(f"   🗑️ Cleaned: {file}")
                except:
                    pass
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
