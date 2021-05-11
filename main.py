from dotenv import load_dotenv
import os
import duolingo
import sys
from pathlib import Path
import pprint
import requests
import random
import genanki
import os.path

# import pykakasi
from furigana.furigana import split_furigana

pp = pprint.PrettyPrinter(indent=2)
# kks = pykakasi.kakasi()

ROOT_DIR = "."
OUTPUT_DIR = "output"
MEDIA_DIR = "media"
DECK_DIR = "deck"

MODEL_ID = 1722919634  # random.randrange(1 << 30, 1 << 31)
DECK_ID = 1185877268  # random.randrange(1 << 30, 1 << 31)


def download_tts(tts: str):
    tts_filename = f"{tts.split('/')[-1]}.mpg"
    tts_path = str(Path(ROOT_DIR, OUTPUT_DIR, MEDIA_DIR, tts_filename))

    if os.path.isfile(tts_path):
        return tts_filename, tts_path

    tts_request = requests.get(tts)
    with open(tts_path, "wb") as f:
        f.write(tts_request.content)

    return tts_filename, tts_path


def pronounce(text: str) -> str:
    result = []
    for pair in split_furigana(text):
        if len(pair) == 2:
            kanji, hira = pair
            result.append(f"<ruby><rb>{kanji}</rb><rt>{hira}</rt></ruby>")
        else:
            result.append(pair[0])
    return "".join(result)


if __name__ == "__main__":
    load_dotenv()

    try:
        username = os.environ["DUOLINGO_USERNAME"]
        password = os.environ["DUOLINGO_PASSWORD"]
    except KeyError:
        print("Missing username or password")
        sys.exit()

    words = dict()

    lingo = duolingo.Duolingo(username, password)
    r = lingo.get_vocabulary()
    vocabs = r["vocab_overview"]
    print("Vocabulary: ", len(vocabs))

    for vocab in vocabs[:5]:
        word = vocab
        word_id = vocab["id"]
        print(word_id, word["word_string"])

        # Get additional data for current word, such as example sentences
        word_definition = lingo.get_word_definition_by_id(word_id)
        word["word_definition"] = word_definition

        words[word_id] = word

    # Download TTS
    Path(ROOT_DIR, OUTPUT_DIR, MEDIA_DIR).mkdir(parents=True, exist_ok=True)
    for word_id, word in words.items():

        word_definition = word["word_definition"]
        tts = word_definition.get("tts", None)
        if tts:
            tts_filename, tts_path = download_tts(tts)
            word_definition["tts_filename"] = tts_filename
            word_definition["tts_local"] = tts_path

        # enable for TTS sentences
        # alternative_forms = word_definition["alternative_forms"]
        # for alternative_form in alternative_forms:
        #     tts = alternative_form.get("tts", None)
        #     if tts is None:
        #         continue
        #     tts_filename, tts_path = download_tts(tts)
        #     alternative_form["tts_filename"] = tts_filename
        #     alternative_form["tts_local"] = tts_path

    # Pronunciation
    for word_id, word in words.items():
        word_definition = word["word_definition"]
        word_definition["pronunciation"] = pronounce(word_definition["word"])

    # Anki Deck
    with open(Path(DECK_DIR, "learning2from_front_template.html"), "r") as file:
        l2f_front_template = file.read()
    with open(Path(DECK_DIR, "learning2from_back_template.html"), "r") as file:
        l2f_back_template = file.read()
    with open(Path(DECK_DIR, "from2learning_front_template.html"), "r") as file:
        f2l_front_template = file.read()
    with open(Path(DECK_DIR, "from2learning_back_template.html"), "r") as file:
        f2l_back_template = file.read()
    with open(Path(DECK_DIR, "styling.css"), "r") as file:
        styling = file.read()

    my_model = genanki.Model(
        MODEL_ID,
        "Duolingo Japanese Model",
        fields=[
            # Basic Fields
            {"name": "FromLanguage"},
            {"name": "LearningLanguage"},
            {"name": "Pronunciation"},
            {"name": "TTS"},  # [sound:sound.mp3]
            # Example Sentences
            {"name": "Example_1"},
            {"name": "ExampleTranslation_1"},
            # {"name": "ExampleTTS_1"},
            {"name": "Example_2"},
            {"name": "ExampleTranslation_2"},
            # {"name": "ExampleTTS_2"},
            {"name": "Example_3"},
            {"name": "ExampleTranslation_3"},
            # {"name": "ExampleTTS_3"},
        ],
        templates=[
            {
                "name": "From to Learning",
                "qfmt": f2l_front_template,
                "afmt": f2l_back_template,
            },
            {
                "name": "Learning to From",
                "qfmt": l2f_front_template,
                "afmt": l2f_back_template,
            },
        ],
        css=styling,
    )

    my_deck = genanki.Deck(DECK_ID, "Duolingo Words")
    media_files = []

    for word_id, word in words.items():
        # Basic fields
        word_definition = word["word_definition"]

        fields = [
            word_definition["translations"],
            word_definition["word"],
            word_definition["pronunciation"],
            f"[sound:{word_definition['tts_filename']}]",
        ]
        media_files.append(word_definition["tts_local"])

        # Example sentences

        alternative_forms = word_definition["alternative_forms"]
        for alternative_form in alternative_forms[:3]:
            example_sentence = pronounce(alternative_form["example_sentence"])
            translation = alternative_form["translation"]
            # tts_local = f"[sound:{alternative_form['tts_filename']}]"
            fields.append(example_sentence)
            fields.append(translation)
            # fields.append(tts_local)
            # media_files.append(alternative_form["tts_local"])

        # Tags
        tags = ["DuolingoWords", word["skill_url_title"]]

        my_note = genanki.Note(guid=word_id, model=my_model, fields=fields, tags=tags)
        my_deck.add_note(my_note)

    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files

    output_file = str(Path(ROOT_DIR, OUTPUT_DIR, "output.apkg"))
    my_package.write_to_file(output_file)
