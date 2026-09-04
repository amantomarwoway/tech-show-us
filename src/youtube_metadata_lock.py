# US LOCK - YouTube Metadata Lock
# Problem A ka fix - Ye file USA category ko lock karegi

YOUTUBE_METADATA_LOCK = {
    "categoryId": "25",  # 25 = News & Politics (USA)
    "privacyStatus": "public",
    "defaultLanguage": "en",
    "defaultAudioLanguage": "en-US",
    "selfDeclaredMadeForKids": False
}

YOUTUBE_DEFAULT_TAGS = [
    "usa news",
    "breaking news",
    "us news today"
]

YOUTUBE_REGION_RESTRICTION = {
    "regionCode": "US",
    "language": "en"
}

def get_locked_metadata():
    return YOUTUBE_METADATA_LOCK

def is_category_locked():
    return YOUTUBE_METADATA_LOCK["categoryId"] == "25"
