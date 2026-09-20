"""
src/learning/ai_code_repair.py - AI CODE REPAIR (no triple-quote bugs)
"""

import os
import re
import json
import ast
import shutil
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

BACKUP_DIR = "data/code_backups"
HISTORY_FILE = "data/repair_history.json"
MAX_FIXES_PER_RUN = 2
MIN_CONFIDENCE = 75


def read_error_logs():
    log_file = "logs/bot.log"
    if not os.path.exists(log_file):
        return []
    try:
        with open(log_file, 'r', errors='ignore') as f:
            content = f.read()
        lines = content.splitlines()[-400:]
        text = "\n".join(lines)
        errors = []
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\s*-\s*(\S+)\s*-\s*(ERROR)\s*-\s*(.+?)(?=\n\d{4}-|\Z)'
        for match in re.finditer(pattern, text, re.DOTALL):
            msg = match.group(4).strip()[:400]
            skip = ['futurewarning', 'deprecation', 'invalid_scope', 'no entries',
                    'rate limit', 'no credits', 'unavailable', 'not_found',
                    '429', '503', '404', 'timeout', 'connection', 'network',
                    'unauthorized', 'ai repair failed', 'render failed',
                    'video file not found', 'ffmpeg failed', 'no stories',
                    'video not created']
            if any(s in msg.lower() for s in skip):
                continue
            errors.append({
                'timestamp': match.group(1),
                'source': match.group(2),
                'message': msg
            })
        return errors[-10:]
    except:
        return []


def extract_file_from_error(error):
    msg = error.get('message', '')
    source = error.get('source', '')
    match = re.search(r'File ["\']([^"\']+\.py)["\']', msg)
    if match:
        return match.group(1)
    if source and source != '__main__':
        return source.replace('.', '/') + '.py'
    return None


def is_fixable_error(error):
    msg = error.get('message', '').lower()
    unfixable = ['api key', 'quota', 'rate limit', 'connection', 'timeout',
                 'network', 'unauthorized', 'forbidden', 'invalid_scope',
                 'no credits', 'unavailable', 'not_found', '503', '404', '429']
    if any(x in msg for x in unfixable):
        return False
    fixable = ['attributeerror', 'nameerror', 'typeerror', 'keyerror',
               'indexerror', 'valueerror', 'importerror', 'modulenotfounderror',
               'syntaxerror', 'indentationerror', 'nonetype',
               'has no attribute', 'not defined', 'unexpected keyword',
               'missing required', 'invalid literal']
    return any(x in msg for x in fixable)


def build_fix_prompt(file_path, file_content, error_msg):
    if len(file_content) > 5000:
        file_content = file_content[:5000] + "\n# ... truncated"

    parts = []
    parts.append("You are an expert Python debugger.")
    parts.append("")
    parts.append("FILE: " + file_path)
    parts.append("")
    parts.append("ERROR:")
    parts.append(error_msg[:500])
    parts.append("")
    parts.append("CODE:")
    parts.append(file_content)
    parts.append("")
    parts.append("RULES:")
    parts.append("1. Fix ONLY the bug. Preserve everything else.")
    parts.append("2. Return valid Python that passes ast.parse().")
    parts.append("3. Be conservative.")
    parts.append("")
    parts.append("OUTPUT JSON:")
    parts.append('{"fixed_code": "full code with \\n escaped", "confidence": 80, "explanation": "what fixed"}')
    parts.append("")
    parts.append('If cannot fix: {"fixed_code": null, "confidence": 0, "explanation": "reason"}')

    return "\n".join(parts)


def call_ai_for_fix(file_path, file_content, error_msg):
    prompt = build_fix_prompt(file_path, file_content, error_msg)

    gk = os.getenv("GEMINI_API_KEY", "")
    if gk:
        try:
            from google import genai
            client = genai.Client(api_key=gk)
            logger.info(f"  Gemini for {file_path}")
            resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            text = getattr(resp, 'text', '')
            result = parse_ai_response(text)
            if result:
                return result
        except Exception as e:
            logger.warning(f"  Gemini fix: {str(e)[:60]}")

    return None


def parse_ai_response(text):
    if not text:
        return None
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group())
        fixed = data.get('fixed_code')
        conf = int(data.get('confidence', 0))
        explanation = data.get('explanation', '')

        if not fixed or conf < MIN_CONFIDENCE:
            return None

        if isinstance(fixed, str):
            fixed = fixed.replace('\\n', '\n').replace('\\t', '\t')

        return {'fixed_code': fixed, 'confidence': conf, 'explanation': explanation}
    except:
        return None


def validate_syntax(code):
    try:
        ast.parse(code)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def create_backup(file_path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(file_path):
        return None
    safe = file_path.replace('/', '_')
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = os.path.join(BACKUP_DIR, f"{safe}.{ts}.bak")
    try:
        shutil.copy2(file_path, backup)
        return backup
    except:
        return None


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_history(h):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(h, f, indent=2)
    except:
        pass


def ai_repair_main():
    logger.info("=" * 60)
    logger.info("AI CODE REPAIR")
    logger.info("=" * 60)

    SELF_FILE = "src/learning/ai_code_repair.py"

    errors = read_error_logs()
    if not errors:
        logger.info("  No errors to fix")
        return {'fixed': 0}

    logger.info(f"  Found {len(errors)} errors")

    file_errors = {}
    for err in errors:
        if not is_fixable_error(err):
            continue
        path = extract_file_from_error(err)
        if not path or path == SELF_FILE:
            continue
        if not os.path.exists(path):
            continue
        if path not in file_errors:
            file_errors[path] = err

    if not file_errors:
        logger.info("  No fixable errors")
        return {'fixed': 0}

    logger.info(f"  {len(file_errors)} files with errors")

    fixed_count = 0
    history = load_history()

    for file_path, error in list(file_errors.items())[:MAX_FIXES_PER_RUN]:
        logger.info(f"\n  Fixing: {file_path}")
        logger.info(f"  Error: {error['message'][:80]}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()
        except:
            continue

        ai_result = call_ai_for_fix(file_path, original, error['message'])
        if not ai_result:
            logger.warning(f"  AI could not fix")
            continue

        valid, msg = validate_syntax(ai_result['fixed_code'])
        if not valid:
            logger.warning(f"  Invalid syntax: {msg}")
            continue

        backup = create_backup(file_path)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ai_result['fixed_code'])

            history.append({
                'timestamp': datetime.now().isoformat(),
                'file': file_path,
                'backup': backup,
                'confidence': ai_result['confidence'],
                'explanation': ai_result['explanation'][:200],
                'status': 'applied'
            })
            save_history(history[-50:])
            fixed_count += 1
            logger.info(f"  FIXED (conf: {ai_result['confidence']}%)")
        except Exception as e:
            logger.error(f"  Apply failed: {e}")
            if backup and os.path.exists(backup):
                shutil.copy2(backup, file_path)

    logger.info(f"  {fixed_count} files fixed")
    return {'fixed': fixed_count}


def verify_last_fix():
    try:
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
    except:
        pass


def rollback_last_fix(file_path):
    history = load_history()
    for entry in reversed(history):
        if entry['file'] == file_path and entry.get('backup'):
            backup = entry['backup']
            if os.path.exists(backup):
                shutil.copy2(backup, file_path)
                entry['status'] = 'rolled_back'
                save_history(history)
                return True
    return False
