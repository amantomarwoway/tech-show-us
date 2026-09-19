"""
src/learning/ai_code_repair.py - AI-POWERED CODE REPAIR
- Reads error logs
- Identifies failed file
- Uses AI (Gemini/GitHub Models) to fix
- Validates syntax before applying
- Backs up + rollback support
"""

import os
import re
import json
import ast
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)


# ============================================================
# CONFIG
# ============================================================

BACKUP_DIR = "data/code_backups"
HISTORY_FILE = "data/repair_history.json"
MAX_FIXES_PER_RUN = 3   # Only 3 files fixed per run (safety)
MIN_CONFIDENCE = 70     # Only apply fixes with confidence >= 70


# ============================================================
# ERROR LOG PARSING
# ============================================================

def read_error_logs():
    """Read recent errors from bot.log"""
    log_file = "logs/bot.log"
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', errors='ignore') as f:
            content = f.read()
        
        # Get last 500 lines
        lines = content.splitlines()[-500:]
        text = "\n".join(lines)
        
        # Find all ERROR + WARNING entries
        errors = []
        
        # Pattern: ERROR - msg OR WARNING - msg
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)\s*-\s*(\S+)\s*-\s*(ERROR|WARNING)\s*-\s*(.+?)(?=\n\d{4}-|\Z)'
        
        for match in re.finditer(pattern, text, re.DOTALL):
            timestamp = match.group(1)
            source = match.group(2)
            level = match.group(3)
            message = match.group(4).strip()[:500]
            
            # Skip expected warnings
            if any(skip in message.lower() for skip in [
                'futurewarning', 'deprecation', 'pandas',
                'invalid_scope', 'no entries', 'rate limit',
                'no credits', 'unavailable', 'not_found',
                '429', '503', '404'
            ]):
                continue
            
            errors.append({
                'timestamp': timestamp,
                'source': source,
                'level': level,
                'message': message
            })
        
        return errors[-20:]  # Last 20 errors
    
    except Exception as e:
        logger.warning(f"Failed to read error logs: {e}")
        return []


def extract_file_from_error(error):
    """Extract file path from error message or traceback"""
    msg = error.get('message', '')
    source = error.get('source', '')
    
    # Try to find file path in traceback
    patterns = [
        r'File ["\']([^"\']+\.py)["\']',
        r'([a-z_]+\.py)',
        r'in (src\.[a-z_.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, msg)
        if match:
            path = match.group(1)
            # Convert module to path
            if not path.endswith('.py'):
                path = path.replace('.', '/') + '.py'
            return path
    
    # Fallback: use source module
    if source and source != '__main__':
        path = source.replace('.', '/') + '.py'
        return path
    
    return None


def is_fixable_error(error):
    """Check if error is actually fixable"""
    msg = error.get('message', '').lower()
    
    # Unfixable / transient
    unfixable = [
        'api key', 'quota', 'rate limit', 'connection',
        'timeout', 'network', 'unauthorized', 'forbidden',
        'invalid_scope', 'no credits', 'unavailable'
    ]
    
    if any(x in msg for x in unfixable):
        return False
    
    # Fixable indicators
    fixable = [
        'attributeerror', 'nameerror', 'typeerror', 'keyerror',
        'indexerror', 'valueerror', 'importerror', 'modulenotfounderror',
        'syntaxerror', 'indentationerror', 'nonetype',
        'has no attribute', 'not defined', 'unexpected keyword',
        'missing required', 'unsupported', 'invalid literal'
    ]
    
    return any(x in msg for x in fixable)


# ============================================================
# AI CALLS
# ============================================================

def call_ai_for_fix(file_path, file_content, error_msg, prev_fix_context=""):
    """Call AI to fix the code. Returns (fixed_code, confidence, explanation) or None"""
    
    # Truncate file content if too large (keep under 8000 chars)
    max_code = 6000
    if len(file_content) > max_code:
        file_content = file_content[:max_code] + "\n# ... (truncated)"
    
    prompt = f"""You are an expert Python debugger. Fix the bug in this file.

FILE: {file_path}

ERROR:
{error_msg[:600]}

CURRENT CODE:
```python
{file_content}
