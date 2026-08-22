from collections import defaultdict
import config
from datetime import datetime, timezone

def verify_stories(stories):
    grouped = defaultdict(list)
    for s in stories:
        key = s['title'].lower()[:40] # Simple grouping by title start
        grouped[key].append(s)

    verified = []
    for key, group in grouped.items():
        if len(group) >= 2: # At least 2 independent sources
            sources = list(set([g['source'] for g in group]))
            if len(sources) >= 2:
                merged = group[0].copy()
                merged['all_sources'] = group
                merged['source_count'] = len(sources)
                merged['verification_score'] = min(0.95, 0.7 + len(sources)*0.1)
                verified.append(merged)
        elif group[0]['source'] in ['reuters','apnews','gov']:
            # Single source allowed only for top-tier official
            g = group[0].copy()
            g['all_sources'] = group
            g['source_count'] = 1
            g['verification_score'] = 0.85
            g['single_source'] = True
            verified.append(g)

    return [s for s in verified if s['verification_score'] >= config.VERIFICATION_THRESHOLD - 0.1]
