
---

## 📄 FILE 2: `src/learning/self_repair.py` (UPDATED)

```python
"""
src/learning/self_repair.py - Self diagnostics + AI repair orchestration
"""

import os
import subprocess
from datetime import datetime, timedelta
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)


def run_self_diagnostics():
    """Full diagnostic + AI repair"""
    logger.info("=" * 60)
    logger.info("🔧 SELF-DIAGNOSTICS + AI REPAIR")
    logger.info("=" * 60)
    
    # Phase 1: Basic health checks
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
        emoji = "✅" if ok else "❌"
        logger.info(f"   {emoji} {name}")
    
    # Phase 2: Basic repairs
    failed_basic = [k for k, v in status.items() if not v]
    if failed_basic:
        logger.warning(f"⚠️ {len(failed_basic)} components failed: {failed_basic}")
        attempt_basic_repairs(failed_basic)
    
    # Phase 3: AI CODE REPAIR (NEW)
    try:
        from src.learning.ai_code_repair import ai_repair_main
        ai_result = ai_repair_main()
        
        if ai_result['fixed'] > 0:
            logger.info(f"🤖 AI fixed {ai_result['fixed']} files!")
            for r in ai_result['errors']:
                logger.info(f"   ✅ {r['file']}: {r['explanation'][:80]}")
    except Exception as e:
        logger.warning(f"AI repair failed: {e}")
    
    # Phase 4: Cleanup
    clean_old_files()
    
    return status


# ============================================================
# BASIC CHECKS (existing)
# ============================================================

def check_gemini():
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
    try:
        token = os.getenv("GITHUB_TOKEN", "")
        if not token:
            return False
        from openai import OpenAI
        client = OpenAI(api_key=token, base_url="https://models.github.ai/inference")
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10
        )
        return bool(resp.choices[0].message.content)
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


# ============================================================
# BASIC REPAIRS
# ============================================================

def attempt_basic_repairs(failed):
    logger.info("=" * 60)
    logger.info("🔨 BASIC REPAIRS")
    logger.info("=" * 60)
    
    for comp in failed:
        if comp == "database":
            repair_database()
        elif comp == "disk":
            clean_old_files()
        elif comp in ["gemini", "github_models"]:
            logger.info(f"   {comp} is external - will retry next run")


def repair_database():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("VACUUM")
        conn.commit()
        conn.close()
        logger.info("   ✅ Database VACUUM'd")
    except Exception as e:
        logger.error(f"   DB repair failed: {e}")


def clean_old_files():
    try:
        from src.config import PATHS
        import glob
        
        cutoff = datetime.now() - timedelta(days=2)
        
        # Clean temp files
        patterns = [
            os.path.join(PATHS['temp'], '*'),
            os.path.join(PATHS.get('output_videos', 'output/videos'), 'short_*.mp4'),
        ]
        
        cleaned = 0
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
            logger.info(f"   🗑️ Cleaned {cleaned} old files")
    except Exception as e:
        logger.error(f"   Cleanup failed: {e}")


# ============================================================
# LAST FIX VERIFICATION - Rollback if failed
# ============================================================

def verify_last_fix():
    """
    If last fix was applied but bot still failing → rollback
    Called at START of next run
    """
    try:
        from src.learning.ai_code_repair import load_history, rollback_last_fix
        
        history = load_history()
        if not history:
            return
        
        # Find last applied fix
        last_fix = None
        for entry in reversed(history):
            if entry.get('status') == 'applied':
                last_fix = entry
                break
        
        if not last_fix:
            return
        
        # Check if error still present in current log
        log_file = "logs/bot.log"
        if not os.path.exists(log_file):
            return
        
        with open(log_file, 'r', errors='ignore') as f:
            recent = f.read()[-10000:]  # Last 10KB
        
        error_snippet = last_fix.get('error', '')[:80]
        
        if error_snippet and error_snippet in recent:
            # Same error again → rollback
            logger.warning(f"⚠️ Last fix failed for {last_fix['file']} - rolling back")
            rollback_last_fix(last_fix['file'])
    except Exception as e:
        logger.debug(f"Verify fix failed: {e}")
