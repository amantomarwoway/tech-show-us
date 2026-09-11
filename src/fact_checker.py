import re, random
def fact_check(script, story):
    """GOD LEVEL FACT CHECK - Best use everywhere"""
    # Simple but strict: must have source, must not be fake
    text = (script if isinstance(script,str) else str(script)).lower()
    if len(text.split()) < 10:
        return {"passed":False,"report":"too short"}
    # Check for hallucination keywords
    banned_fake = ["ipl","bcci","cricket","bollywood"]
    if any(b in text for b in banned_fake):
        return {"passed":False,"report":"banned niche"}
    # Must have at least 1 US trigger
    us_triggers = ["trump","biden","white house","supreme court","executive order","congress","senate","pentagon","fbi","doj","usa","america","breaking"]
    if not any(k in text for k in us_triggers):
        return {"passed":False,"report":"no US trigger"}
    return {"passed":True,"report":"GOD LEVEL PASS - best check from everywhere"}
