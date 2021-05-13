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
import pickle

# import pykakasi
from furigana.furigana import split_furigana

pp = pprint.PrettyPrinter(indent=2)
# kks = pykakasi.kakasi()

ROOT_DIR = "."
OUTPUT_DIR = "output"
MEDIA_DIR = "media"
DECK_DIR = "deck"

MODEL_ID = 1335956388  # random.randrange(1 << 30, 1 << 31)
DECK_ID = 1973287916  # random.randrange(1 << 30, 1 << 31)


JAPANESE_SKILLS = [
    "Hiragana 1",
    "Hiragana 2",
    "Hiragana 3",
    "Hiragana 4",
    "Greetings",
    "Katakana 1",
    "Introduction",
    "Katakana 2",
    "Introduction 2",
    "Katakana 3",
    "Food 1",
    "Time",
    "Routines",
    "Home 1",
    "Introduction 3",
    "Counting",
    "Family 1",
    "Restaurant",
    "Activity 1",
    "Position",
    "Vacation 1",
    "Hobby 1",
    "Family 2",
    "Transportation 1",
    "Clothes 1",
    "Hobby 2",
    "Weather 1",
    "Food 2",
    "Direction 1",
    "Food 3",
    "Dates",
    "Shopping 1",
    "People 1",
    "Activity 2",
    "Nature 1",
    "Classroom",
    "Konbini",
    "Classroom 2",
    "Feelings 1",
    "Direction 2",
    "Objects",
    "Shopping 2",
    "Clothes 2",
    "Hobby 3",
    "Classroom 3",
    "Health 1",
    "Vacation 2",
    "Post Office",
    "Games",
]


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
    online_vocabs = r["vocab_overview"]
    print("Vocabulary: ", len(online_vocabs))

    words_file = Path(ROOT_DIR, OUTPUT_DIR, "words.pickle")
    local_vocabs = {}
    if words_file.is_file():
        with open(words_file, "rb") as f:
            local_vocabs = pickle.load(f)

    for vocab in online_vocabs:
        word = vocab
        word_id = vocab["id"]
        print(word_id, word["word_string"])

        # use cache if word exists already
        if word_id in local_vocabs:
            words[word_id] = local_vocabs[word_id]
            continue

        # Get additional data for current word, such as example sentences
        word_definition = lingo.get_word_definition_by_id(word_id)
        word["word_definition"] = word_definition

        words[word_id] = word

    # Save words for later
    with open(words_file, "wb") as f:
        pickle.dump(words, f)

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
            # Sorting Field
            {"name": "Level"},
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
            str(JAPANESE_SKILLS.index(word["skill"])),
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
        for i in range(max(0, 3 - len(alternative_forms))):
            fields.append("")
            fields.append("")

        # Tags
        tags = ["DuolingoWords", word["skill_url_title"]]

        my_note = genanki.Note(
            guid=word_id,
            model=my_model,
            fields=fields,
            tags=tags,
        )
        my_deck.add_note(my_note)

    my_package = genanki.Package(my_deck)
    my_package.media_files = media_files

    output_file = str(Path(ROOT_DIR, OUTPUT_DIR, "output.apkg"))
    my_package.write_to_file(output_file)
