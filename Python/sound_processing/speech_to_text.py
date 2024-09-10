"""Decoder for extracting uttered number during game.

Alessandro De Luca - 25.08.2022
"""
import speech_recognition as sr

# init recognizer
asr_model = sr.Recognizer()


def record2():
    """Continuous recording and transcription with a ~5 sec delay.
    """

    try:
        with sr.Microphone() as mic_source:
            print("Recording...")

            audio = asr_model.listen(mic_source)

            # use google's sr
            transciption = asr_model.recognize_google(audio, language="en")

            print(transciption)

    except sr.RequestError as e:
        print(f"Could not request result:\n\t{e}")

    except sr.UnknownValueError as e:
        print(f"Unknown error occured:\n\t{e}")


def main():
    while(True):
        record2()


if __name__ == "__main__":
    main()
