"""
src/learning/self_repair.py - Self-repair + diagnostics
- Gemini / GitHub Models checks REMOVED (no AI in pipeline)
- AI code repair REMOVED (was Gemini-based)
- Only local checks remain
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
        "pexels": check_pexels(),
        "youtube": check_youtube(),
        "database": check_database(),
        "disk": check_disk(),
        "tts": check_tts(),
        "ffmpeg": check_ffmpeg(),
    }

    for name, ok in status.items():
        emoji = "OK" if ok else "FAIL"
        logger.info(f"   [{emoji}] {name}")

    failed = [k for k, v in status.items() if not v]
    if failed:
        logger.warning(f"{len(failed)} failed: {failed}")
        attempt_basic_repairs(failed)

    clean_old_files()
    free_memory()

    return status


def check_pexels():
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
    except Exception:
        return False


def check_youtube():
    cid = os.getenv("YT_CLIENT_ID", "")
    csec = os.getenv("YT_CLIENT_SECRET", "")
    rt = os.getenv("YT_REFRESH_TOKEN", "")
    return all([cid, csec, rt])


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


def attempt_basic_repairs(failed):
    for comp in failed:
        if comp == "database":
            repair_database()
        elif comp == "disk":
            clean_old_files()


def repair_database():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("VACUUM")
        conn.commit()
        conn.close()
        logger.info("   Database VACUUM'd")
    except Exception as e:
        logger.error(f"   DB repair: {e}")


def clean_old_files():
    try:
        from src.config import PATHS
        cutoff = datetime.now() - timedelta(days=2)
        cleaned = 0

        patterns = [
            os.path.join(PATHS['temp'], '*'),
        ]

        for pattern in patterns:
            for file in glob.glob(pattern):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file))
                    if mtime < cutoff:
                        os.remove(file)
                        cleaned += 1
                except Exception:
                    pass

        if cleaned > 0:
            logger.info(f"   Cleaned {cleaned} old files")
    except Exception as e:
        logger.error(f"   Cleanup: {e}")


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
            logger.info(f"   Memory freed: {freed} files")
    except Exception as e:
        logger.debug(f"Memory free: {e}")


def verify_last_fix():
    """No-op — AI code repair removed."""
    return
