import os
import openai

API_KEY = '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'
openai.api_key = API_KEY
model_id = 'whisper-1'

#下面括号里的音频名称可自定义
audio_file = open("audio.wav", "rb")

transcript = openai.Audio.transcribe("whisper-1", audio_file)

print(transcript.text)