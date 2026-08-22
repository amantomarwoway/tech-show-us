import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import os, traceback
from news_fetcher import fetch_all_news
from source_verifier import verify_stories
from trend_score import score_and_rank
from duplicate_detector import is_duplicate
from script_generator import generate_script
from fact_checker import fact_check
from video_generator import create_video
from thumbnail_generator import create_thumbnail
from youtube_uploader import upload_video
from database import init_db, save_story, mark_uploaded

def main():
    init_db()
    print(f"1. Fetching USA news from RSS...")
    raw_stories = fetch_all_news()
    if not raw_stories:
        print("No news fetched"); return

    print(f"2. Verifying {len(raw_stories)} stories...")
    verified = verify_stories(raw_stories)

    print(f"3. Scoring & Ranking...")
    ranked = score_and_rank(verified)

    for story in ranked:
        if is_duplicate(story):
            print(f"Skipping duplicate: {story['title']}")
            continue

        story_id = save_story(story)

        print(f"4. Generating script for: {story['title']}")
        script_data = generate_script(story)
        if not script_data: continue

        print(f"5. Fact Checking script...")
        validation = fact_check(script_data['script'], story)
        if not validation['passed']:
            print(f"Fact check FAILED: {validation['report']}")
            continue

        print(f"6. Creating video...")
        video_path = create_video(script_data, story)
        thumb_path = create_thumbnail(script_data, story)

        print(f"7. Uploading to YouTube...")
        yt_id = upload_video(video_path, thumb_path, script_data, story)

        if yt_id:
            mark_uploaded(story_id, yt_id)
            print(f"8. UPLOADED: https://youtu.be/{yt_id}")
            break # Sirf 1 video per run

if __name__ == "__main__":
    try: main()
    except Exception as e:
        traceback.print_exc()
        with open("logs.txt","w") as f: f.write(traceback.format_exc())
