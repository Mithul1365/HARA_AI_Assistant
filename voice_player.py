import hashlib
import json
import os
import sys
import pyttsx3


def progress_path_for(text):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    base = os.path.join(os.environ.get("TEMP", "."), f"hara_voice_{digest}.json")
    return base


def save_progress(path, text, location, completed=False):
    data = {
        "text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "location": max(0, int(location)),
        "completed": bool(completed),
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def main():
    if len(sys.argv) < 2:
        return

    text = sys.argv[1]
    try:
        start_location = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    except ValueError:
        start_location = 0

    progress_path = progress_path_for(text)
    start_location = max(0, min(start_location, len(text)))

    # Resume from the last word position saved by pyttsx3/SAPI5.
    remaining = text[start_location:].lstrip()
    if not remaining:
        save_progress(progress_path, text, len(text), completed=True)
        return

    # Find the character offset of the remaining text in the original.
    actual_start = len(text) - len(remaining)

    engine = pyttsx3.init()
    engine.setProperty("rate", 170)

    def on_started_word(name, location, length):
        # location is relative to the current utterance.
        current = actual_start + max(0, int(location))
        save_progress(progress_path, text, current, completed=False)

    engine.connect("started-word", on_started_word)

    save_progress(progress_path, text, actual_start, completed=False)

    engine.say(remaining)
    engine.runAndWait()

    save_progress(progress_path, text, len(text), completed=True)


if __name__ == "__main__":
    main()
