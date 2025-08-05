from google.cloud.speech import RecognitionAudio, RecognitionConfig, SpeechAsyncClient
from google.api_core.exceptions import InvalidArgument

async def transcribe(client: SpeechAsyncClient, data: bytes, *, sample_rate: int = 16000, language: str = "he-IL") -> str:
    audio = RecognitionAudio(content=data)
    config = RecognitionConfig(
        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code=language,
    )
    try:
        response = await client.recognize(config=config, audio=audio)
    except InvalidArgument as e:
        return "Audio too long to transcribe"
    if not response.results:
        return ""
    return response.results[0].alternatives[0].transcript
