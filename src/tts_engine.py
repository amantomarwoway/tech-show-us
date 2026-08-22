import os, wave

def generate_voice(text, out_path="output/voice.wav"):
    os.makedirs("output", exist_ok=True)
    try:
        from piper import PiperVoice
        voice = PiperVoice.load("piper_model/en_US-amy-medium.onnx")
        with wave.open(out_path, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(22050)
            for chunk in voice.synthesize(text):
                wf.writeframes(chunk.audio_int_16_bytes)
        return out_path
    except Exception as e:
        print(f"Piper fail {e}, using espeak-ng fallback")
        os.system(f'espeak-ng -v en-us "{text}" -s 155 --stdout > {out_path}')
        return out_path
