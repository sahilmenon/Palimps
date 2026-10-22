
# Palimps: The Endless Sentence Generator

Palimps harnesses the power of Markov chains to create endless, evolving sentences from a diverse corpus of text files. Inspired by ancient manuscripts, palimpsests that bear traces of their past, this program layers words and phrases to generate text that is both unpredictable and evocative.

## Table of Contents

- [Overview](#palimps-the-endless-sentence-generator)
- [Backstory & Origin](#backstory--origin)
- [The Math Behind Markov Chains](#the-math-behind-markov-chains)
- [Features](#features)
- [How It Works: Code Overview](#how-it-works-code-overview)
- [Running the Program](#running-the-program)
- [Dependencies](#dependencies)
- [Conclusion](#conclusion)

---

## Backstory & Origin

The name **Palimps** is a nod to the historical palimpsest—a manuscript that has been reused, where traces of earlier writings remain visible beneath the new text. This concept mirrors our approach: using old words to inspire new sentences. Just as scribes would erase and rewrite, leaving behind hints of what once was, Palimps builds upon previous words to continuously reinvent language, celebrating both legacy and innovation.

---

## The Math Behind Markov Chains

At its core, Palimps relies on Markov chains, a type of stochastic model where the probability of each subsequent word depends solely on a fixed number of preceding words. Key concepts include:

- **Order of the Chain:**
  The program typically uses an order of 3, meaning that every group of three words predicts the next word. This parameter can be adjusted, influencing the balance between randomness and coherence.

- **Chain Construction:**
  The program tokenizes sentences and records sequences of words along with their following word. This mapping creates a "chain" that encapsulates the structure and patterns of the source text.

- **Backoff Strategy:**
  When the current word sequence is not found in the chain, the program gracefully reduces the context (backoff) to continue generating text without interruption.

- **Grammatical Validation:**
  To ensure readability, the program uses natural language processing (via NLTK) to check that corpus sentences contain essential grammatical elements such as verbs and balanced punctuation before they are added to the chain.

---

## Features

- **Corpus Ingestion:**
  Recursively loads and concatenates text files from a specified folder to form a diverse input corpus.

- **Customizable Chain Order:**
  Users can experiment with different orders of the Markov chain, affecting the generated text's structure and flow.

- **Caching Mechanism:**
  Once built, the Markov chain is saved (using Python's `pickle` module) to reduce future build times, unless a forced rebuild is specified.

- **Optional Starting Phrase:**
  The tool supports a custom starting phrase, guiding the direction of the generated text while still embracing randomness.

- **Novelty Checking:**
  Generated output is checked against the source corpus using 7-word n-gram matching. If the output contains any passage that appears verbatim in the source, a warning is printed. This prevents the chain from simply copy-pasting long runs of original text. Disable with `--no-novelty-check` for faster generation.

- **Smart Detokenization:**
  After generation, a regex-based detokenizer reconstructs natural-reading text from NLTK tokens — correctly handling contractions (`don't`, `it's`, `they're`), punctuation spacing, brackets, and quotation marks.

- **Safe Generation Loop:**
  An iteration cap (`10,000` steps) prevents the generator from hanging if the chain cannot reach a sentence-final punctuation mark. A warning is printed and the output is closed gracefully if the limit is hit.

---

## How It Works: Code Overview

1. **Corpus Loading:**
   The program traverses a user-specified folder to read all `.txt` files, combining them into one large corpus.

2. **Sentence Tokenization & Validation:**
   Using NLTK, the text is divided into sentences. Each sentence is validated for grammatical integrity — ensuring it contains at least one verb and balanced punctuation — before being added to the chain.

3. **Building the Markov Chain:**
   For each valid sentence, the program tokenizes the text and builds a mapping of word sequences (of a user-defined order) to possible following words.

4. **Text Generation:**
   Starting from either a random or user-specified sequence, the program iteratively selects the next word based on the Markov chain, applying a backoff strategy when necessary to maintain flow. Generation halts when the target word count is reached and the output ends on a sentence boundary.

5. **Novelty Check:**
   The completed output is scanned for 7-word n-grams that appear verbatim in the source corpus. A warning is shown if any match is found.

6. **Caching:**
   The constructed chain, starting tokens, and valid source sentences are saved to a `.pkl` cache file to speed up subsequent runs.

---

## Running the Program

To generate text with Palimps, run the script with the appropriate arguments. For example:

```bash
python main.py --input path/to/text_files --output generated_text.txt --num_words 1000 --order 3
```

**Command-Line Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | *(required)* | Folder containing `.txt` files for the corpus |
| `--output` | `generated_text.txt` | File where the generated text will be saved |
| `--num_words` | `1000` | Target word count for the generated text |
| `--order` | `3` | Order of the Markov chain |
| `--rebuild` | `False` | Force a rebuild of the chain even if a cache exists |
| `--start` | *(none)* | Optional starting phrase for text generation |
| `--no-novelty-check` | `False` | Disable novelty checking (faster, may echo source text) |

**Note:** If you have an older cached `.pkl` file that predates novelty checking, run with `--rebuild` once to regenerate the cache with the required data.

---

## Dependencies

- **Python 3.x**
- **NLTK** — Natural Language Toolkit for tokenization and part-of-speech tagging
- **Standard Libraries:** `os`, `re`, `glob`, `random`, `argparse`, `sys`, `pickle`

NLTK resources (`punkt`, `averaged_perceptron_tagger`) are downloaded automatically on first run. To install NLTK manually:

```bash
pip install nltk
```
