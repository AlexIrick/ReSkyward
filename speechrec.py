import speech_recognition as sr
import pyttsx3


def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, 0.5)
        try:
            audio = recognizer.listen(source, 5, 5)
        except sr.WaitTimeoutError:
            return ''

    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


def start_stt():
    print("Started STT")
    r = sr.Recognizer()

    # Get mic
    mic = sr.Microphone()
    guess = recognize_speech_from_mic(r, mic)
    if guess is not None and guess and guess["transcription"]:
        print(f'You said: {guess["transcription"]}')
        return guess["transcription"]



# Python program to translate
# speech to text and text to speech


if __name__ == "__main__":
    # Initialize the recognizer
    r = sr.Recognizer()

    # Get mic
    mic = sr.Microphone()

    guess = recognize_speech_from_mic(r, mic)
    print(f'You said: {guess["transcription"]}')


