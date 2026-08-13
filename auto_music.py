# auto_music.py - TECH4USA ke liye
# Ye file topic dekh ke Pixabay se direct koi sa bhi background music le legi

import requests
import random

# Yahan apni Pixabay API Key daal de - pixabay.com/api/docs/ se free me milti hai
PIXABAY_KEY = "PASTE_YOUR_KEY_HERE"

def fetch_music_for_video(topic):
    """
    Topic dega -> 5 music search karega -> 1 random select karke dega
    """
    try:
        # Topic ko search query banaya
        # Example: topic = "iPhone 16" -> search = "iPhone 16 technology"
        search_query = f"{topic} technology"
        
        print(f"🎵 TECH4USA: '{topic}' ke liye Pixabay se music search ho raha hai...")
        
        # Pixabay se 5 music maang raha hu
        api_url = f"https://pixabay.com/api/music/?key={PIXABAY_KEY}&q={search_query}&per_page=5"
        response = requests.get(api_url).json()

        # Agar is topic ka na mile to default tech music le lega
        if response['total'] == 0:
            print("Is topic ka music nahi mila, default tech music le raha hu...")
            api_url = f"https://pixabay.com/api/music/?key={PIXABAY_KEY}&q=technology background&per_page=5"
            response = requests.get(api_url).json()

        # 5 me se 1 random music select
        random_track = random.choice(response['hits'])
        music_url = random_track['audio'] # direct mp3 link
        
        print(f"✅ Music mil gaya: {random_track['tags']} | Duration: {random_track['duration']}s")

        # Direct download
        music_data = requests.get(music_url).content
        temp_path = "temp_bg_music.mp3"
        with open(temp_path, "wb") as f:
            f.write(music_data)

        print("✅ Background music ready hai!")
        return temp_path

    except Exception as e:
        print(f"❌ Music Error: {e}")
        return None
