"""Standalone three-response TTS diagnostic for Velvet."""

from voice import VoiceInterface

voice = VoiceInterface()
try:
    voice.speak("Velvet voice test one is working.")
    voice.speak("Velvet voice test two is working.")
    voice.speak("Velvet voice test three is working.")
    voice.wait_until_done()
    print("All three voice tests completed.")
finally:
    voice.shutdown()
