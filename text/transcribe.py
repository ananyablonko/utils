import typing
from google.cloud.speech import RecognitionAudio, RecognitionConfig, RecognizeResponse, SpeechClient


def transcribe(client: SpeechClient, data: bytes, *, sample_rate: int = 16000, language: str = "he-IL") -> str:
    audio = RecognitionAudio(content=data)
    config = RecognitionConfig(
        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code=language,
    )
    response = typing.cast(RecognizeResponse, client.recognize(config=config, audio=audio))
    if not response.results:
        return ""
    return response.results[0].alternatives[0].transcript
