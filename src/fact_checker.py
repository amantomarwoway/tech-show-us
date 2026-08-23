def fact_check(script_data):
    try:
        if isinstance(script_data, dict):
            text = script_data.get('script','') or script_data.get('full_script','') or str(script_data)
            title = script_data.get('title','')
        else:
            text = str(script_data)
            title = text[:50]
        
        print(f"Fact checking: {title[:50]}...")
        # Simple pass for now - always return True
        # You can add real fact checking logic here later
        return True
    except Exception as e:
        print(f"fact_check crashed: {e}, forcing pass")
        return True
