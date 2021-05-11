# Duolingo Words

Download Duolingo Words into usable format (Anki, CSV, ...)

## Development 

Phase 1: Simple Plugin that creates a deck, downloads sounds, etc. 
Phase 2: More general class + CLI tool, that download words into any format (CSV, JSON, Anki Deck, ...)

## Architecture

```
Duolingo --- Duolingo Words
              |- CSV
              |- Anki Generated Deck
              |- Anki Plugin
```

## Ideas

### Anki (using python CLI)

- design similar to Duolingo
- furigana support
- example sentences
- TTS for word and example sentences
- multiple accounts support
- deck generation using https://github.com/kerrickstaley/genanki

### CSV (using python CLI)

- list of supported attributes

### Anki Plugin

- Enter Username + Password and download all cards
- Generate deck automatically
- use Duolingo Words as download step

