"""
src/learning/self_repair.py - local diagnostics only
"""

import os
import subprocess
import glob
from datetime import datetime, timedelta
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)


def run_self_diagnostics():
    logger.info("=" * 60)
    logger.info("SELF-DIAGNOSTICS (local only)")
    logger.info("=" * 60)

    status = {
        "youtube": check_youtube(),
        "database": check_database(),
        "disk": check_disk(),
        "tts": check_tts(),
        "ffmpeg": check_ffmpeg(),
    }

    for name, ok in status.items():
        emoji = "OK" if ok else "FAIL"
        logger.info(f"   [{emoji}] {name}")

    clean_old_files()
    free_memory()
    return status


def check_youtube():
    return all([os.getenv("YT_CLIENT_ID", ""),
                os.getenv("YT_CLIENT_SECRET", ""),
                os.getenv("YT_REFRESH_TOKEN", "")])


def check_database():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stories")
        cur.fetchone()
        conn.close()
        return True
    except Exception:
        return False


def check_disk():
    try:
        stat = os.statvfs('/')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
        logger.info(f"   Disk free: {free_gb:.1f} GB")
        return free_gb > 1
    except Exception:
        return True


def check_tts():
    try:
        import piper  # noqa
        return True
    except Exception:
        return False


def check_ffmpeg():
    try:
        r = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def clean_old_files():
    try:
        from src.config import PATHS
        cutoff = datetime.now() - timedelta(days=2)
        cleaned = 0
        for file in glob.glob(os.path.join(PATHS['temp'], '*')):
            try:
                if datetime.fromtimestamp(os.path.getmtime(file)) < cutoff:
                    os.remove(file)
                    cleaned += 1
            except Exception:
                pass
        if cleaned > 0:
            logger.info(f"   Cleaned {cleaned} old files")
    except Exception as e:
        logger.error(f"Cleanup: {e}")


def free_memory():
    try:
        from src.config import PATHS
        freed = 0
        for ext in ['*.png', '*.mp4', '*.jpg']:
            for f in glob.glob(os.path.join(PATHS['temp'], ext)):
                try:
                    os.remove(f)
                    freed += 1
                except Exception:
                    pass
        if freed > 0:
            logger.info(f"   Freed {freed} files")
    except Exception:
        pass


def verify_last_fix():
    return
