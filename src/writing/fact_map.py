"""
src/writing/fact_map.py - Map sentences to sources
"""

import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_fact_map(script_text, sources):
    """
    Create FACT_MAP linking each factual sentence to a source
    
    Returns:
        list of {
            sentence_id, factual_claim, source_url, 
            source_type, publication_time, confidence, verification_status
        }
    """
    if not script_text:
        return []
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', script_text)
    
    fact_map = []
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        
        if len(sentence) < 10:
            continue
        
        # Skip questions and opinions
        if sentence.endswith('?'):
            continue
        if sentence.lower().startswith(('i think', 'maybe', 'perhaps', 'in my opinion')):
            continue
        
        # Find matching source
        source = match_source(sentence, sources)
        
        fact_map.append({
            'sentence_id': i,
            'factual_claim': sentence,
            'source_url': source.get('url', ''),
            'source_type': source.get('type', 'unknown'),
            'publication_time': source.get('time', ''),
            'confidence': source.get('confidence', 50),
            'verification_status': 'pending'
        })
    
    return fact_map


def match_source(sentence, sources):
    """Find best matching source for a sentence"""
    if not sources:
        return {}
    
    sentence_lower = sentence.lower()
    
    best_match = {}
    best_score = 0
    
    for source in sources:
        source_text = source.get('title', '').lower()
        
        # Simple keyword overlap
        sent_words = set(re.findall(r'\w+', sentence_lower)) - {'the', 'a', 'an'}
        src_words = set(re.findall(r'\w+', source_text)) - {'the', 'a', 'an'}
        
        if not sent_words or not src_words:
            continue
        
        overlap = len(sent_words & src_words)
        score = overlap / max(len(sent_words), len(src_words))
        
        if score > best_score:
            best_score = score
            best_match = source
    
    return best_match


def validate_fact_map(fact_map):
    """
    Validate that all factual sentences have sources
    
    Returns:
        dict with validation status and unsourced claims
    """
    unsourced = []
    
    for item in fact_map:
        if not item.get('source_url'):
            unsourced.append(item['factual_claim'])
    
    return {
        'valid': len(unsourced) == 0,
        'unsourced_count': len(unsourced),
        'unsourced_claims': unsourced
    }
