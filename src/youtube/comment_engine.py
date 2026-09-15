"""
src/youtube/comment_engine.py - Comment reply engine
"""

import os
import random
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

REPLY_TEMPLATES = [
    "Great point! What do you think should happen next?",
    "Interesting perspective. Do you think this will change things?",
    "Thanks for watching! What's your take on this?",
    "Good question. We're following this story closely.",
    "Appreciate the comment! Stay tuned for updates.",
    "That's a fair point. What would you do differently?",
    "Thanks for engaging! This is definitely a developing story.",
    "Good observation. What do you think the impact will be?",
    "Thanks for watching! More updates coming soon.",
    "Valid point. Do you think this affects you directly?"
]

def reply_to_comments(video_id, max_replies=10):
    """
    Fetch first 10 comments and reply with witty/provocative responses
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        client_id = os.getenv("YT_CLIENT_ID", "")
        client_secret = os.getenv("YT_CLIENT_SECRET", "")
        refresh_token = os.getenv("YT_REFRESH_TOKEN", "")
        
        if not all([client_id, client_secret, refresh_token]):
            logger.warning("YouTube credentials missing - skipping comments")
            return 0
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
        )
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Fetch comments
        response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_replies,
            textFormat='plainText',
            order='time'
        ).execute()
        
        threads = response.get('items', [])
        
        if not threads:
            logger.info(f"No comments to reply to for {video_id}")
            return 0
        
        replies_sent = 0
        
        for thread in threads[:max_replies]:
            try:
                comment_id = thread['id']
                comment_text = thread['snippet']['topLevelComment']['snippet']['textDisplay']
                
                # Generate witty reply
                reply_text = generate_reply(comment_text)
                
                # Post reply
                youtube.comments().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'parentId': comment_id,
                            'textOriginal': reply_text
                        }
                    }
                ).execute()
                
                replies_sent += 1
                logger.info(f"Replied to comment: {comment_text[:30]}...")
                
                # Rate limit
                import time
                time.sleep(1)
            
            except Exception as e:
                logger.warning(f"Reply failed: {e}")
                continue
        
        logger.info(f"Comment replies: {replies_sent}/{max_replies}")
        return replies_sent
    
    except Exception as e:
        logger.error(f"Comment engine failed: {e}")
        return 0


def generate_reply(comment_text):
    """Generate witty/provocative reply based on comment"""
    comment_lower = comment_text.lower()
    
    # Context-aware replies
    if any(w in comment_lower for w in ['agree', 'yes', 'right', 'true']):
        replies = [
            "Exactly! This needs more attention.",
            "Glad someone sees it clearly. What should happen next?",
            "You're absolutely right. This is bigger than people think."
        ]
    elif any(w in comment_lower for w in ['disagree', 'no', 'wrong', 'fake']):
        replies = [
            "Interesting take. What would you say to those who disagree?",
            "Fair enough. What evidence would change your mind?",
            "Respect your opinion. What's your alternative view?"
        ]
    elif any(w in comment_lower for w in ['?', 'how', 'why', 'what']):
        replies = [
            "Great question. We're looking into this.",
            "That's the key question everyone's asking.",
            "We'll have more on this soon. Stay tuned."
        ]
    else:
        replies = REPLY_TEMPLATES
    
    return random.choice(replies)
