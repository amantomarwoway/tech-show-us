import os, sys, time, random
sys.path.append(os.path.join(os.path.dirname(__file__),'src'))
from src.config import GOD_INSTRUCTION, USER_AGENTS, pro_headers, pro_fetch
from src.database import init_db, save_story, mark_uploaded
from src.research_god import research_god_main
from src.editor_god import editor_god_main
from src.boss_approval import boss_approval_main
from src.uploader_god import uploader_god_main
from src.self_evolution import self_evolution_main

print(GOD_INSTRUCTION)

def main():
    print("===== 5 BRAIN NO FALLBACK START =====")
    init_db()
    stories = research_god_main()  # Brain 1 - 45 sec scan, no fallback, force fetch
    if not stories:
        raise RuntimeError("Research God failed - no fallback allowed")
    for cand in stories[:3]:
        print(f"Checking {cand['title'][:60]}")
        editor_data = editor_god_main(cand)  # Brain 2 - force visuals 1.0s + 1.8s
        video_path = editor_data.get('video_path')
        if not video_path or not os.path.exists(video_path):
            raise RuntimeError(f"Editor God failed - video not created {video_path}")
        boss_data = boss_approval_main(video_path, editor_data, cand)  # Brain 3 - force 50 countries
        if not boss_data.get('approved') or boss_data.get('score',0)<90:
            print(f"[BOSS] REJECTED {boss_data.get('score')} - auto-delete - NO FALLBACK")
            try: os.remove(video_path)
            except: pass
            continue
        story_id = save_story({**cand, **editor_data})
        yt_ids = uploader_god_main(video_path, editor_data, cand, boss_data)  # Brain 4 - force per country
        if not yt_ids:
            raise RuntimeError("Uploader God failed - no fallback")
        mark_uploaded(story_id, str(yt_ids))
        break
    self_evolution_main()  # Brain 5 - force rewrite 1% better
    print("===== 5 BRAIN DONE NO FALLBACK =====")

if __name__=="__main__":
    main()
