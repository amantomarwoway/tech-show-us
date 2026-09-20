"""
src/learning/self_repair.py - Self-repair + diagnostics (FIXED)
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
    logger.info("SELF-DIAGNOSTICS + AI REPAIR")
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

    for name, ok in status.items():
        emoji = "OK" if ok else "FAIL"
        logger.info(f"   [{emoji}] {name}")

    failed = [k for k, v in status.items() if not v]
    if failed:
        logger.warning(f"{len(failed)} failed: {failed}")
        attempt_basic_repairs(failed)

    try:
        from src.learning.ai_code_repair import ai_repair_main
        ai_result = ai_repair_main()
        if ai_result['fixed'] > 0:
            logger.info(f"AI fixed {ai_result['fixed']} files")
    except Exception as e:
        logger.warning(f"AI repair: {e}")

    clean_old_files()
    free_memory()

    return status


def check_gemini():
    try:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            return False
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-3.6-flash", contents="Say OK")
        return bool(getattr(resp, 'text', ''))
    except:
        return False


def check_github_models():
    """Correct endpoints"""
    try:
        token = os.getenv("GITHUB_TOKEN", "")
        if not token:
            return False
        from openai import OpenAI

        endpoints = [
            "https://models.inference.ai.azure.com",
            "https://models.github.ai/inference",
        ]
        for endpoint in endpoints:
            try:
                client = OpenAI(api_key=token, base_url=endpoint)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5
                )
                if resp.choices[0].message.content:
                    return True
            except:
                continue
        return False
    except:
        return False


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
    except:
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
    except:
        return False


def check_disk():
    try:
        stat = os.statvfs('/')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        logger.info(f"   Disk free: {free_gb:.1f} GB")
        return free_gb > 1
    except:
        return True


def check_tts():
    try:
        import piper
        return True
    except:
        return False


def check_ffmpeg():
    try:
        r = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False


def attempt_basic_repairs(failed):
    for comp in failed:
        if comp == "database":
            repair_database()
        elif comp == "disk":
            clean_old_files()
        elif comp in ["gemini", "github_models"]:
            logger.info(f"   {comp} is external - retry next run")


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
            os.path.join(PATHS.get('output_videos', 'output/videos'), 'short_*.mp4'),
            os.path.join(PATHS.get('output_videos', 'output/videos'), 'text_*.mp4'),
        ]

        for pattern in patterns:
            for file in glob.glob(pattern):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file))
                    if mtime < cutoff:
                        os.remove(file)
                        cleaned += 1
                except:
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
                except:
                    pass

        if freed > 0:
            logger.info(f"   Memory freed: {freed} files")
    except Exception as e:
        logger.debug(f"Memory free: {e}")


def verify_last_fix():
    try:
        from src.learning.ai_code_repair import load_history, rollback_last_fix
        history = load_history()
        if not history:
            return
        last = None
        for entry in reversed(history):
            if entry.get('status') == 'applied':
                last = entry
                break
        if not last:
            return
        log_file = "logs/bot.log"
        if not os.path.exists(log_file):
            return
        with open(log_file, 'r', errors='ignore') as f:
            recent = f.read()[-8000:]
        error_snippet = last.get('error', '')[:80]
        if error_snippet and error_snippet in recent:
            logger.warning(f"Last fix failed - rolling back {last['file']}")
            rollback_last_fix(last['file'])
    except:
        pass
