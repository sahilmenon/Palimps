
# Palimps: The Endless Sentence Generator

Palimps harnesses the power of Markov chains to create endless, evolving sentences from a diverse corpus of text files. Inspired by ancient manuscripts—palimpsests that bear traces of their past—this program layers words and phrases to generate text that is both unpredictable and evocative.

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
  To ensure readability, the program uses natural language processing (via NLTK) to check that generated sentences contain essential grammatical elements such as verbs and balanced punctuation.

---

## Features

- **Corpus Ingestion:**  
  Recursively loads and concatenates text files from a specified folder to form a diverse input corpus.

- **Customizable Chain Order:**  
  Users can experiment with different orders of the Markov chain, affecting the generated text's structure and flow.

- **Caching Mechanism:**  
  Once built, the Markov chain is saved (using Python’s `pickle` module) to reduce future build times, unless a forced rebuild is specified.

- **Optional Starting Phrase:**  
  The tool supports a custom starting phrase, guiding the direction of the generated text while still embracing randomness.

- **Smart Punctuation Handling:**  
  After text generation, the program refines punctuation to improve the overall readability and flow of the output.

---

## How It Works: Code Overview

1. **Corpus Loading:**  
   The program traverses a user-specified folder to read all `.txt` files, combining them into one large corpus.

2. **Sentence Tokenization & Validation:**  
   Using NLTK, the text is divided into sentences. Each sentence is validated for grammatical integrity—ensuring it contains verbs and balanced punctuation.

3. **Building the Markov Chain:**  
   For each valid sentence, the program tokenizes the text and builds a mapping of word sequences (of a user-defined order) to possible following words.

4. **Text Generation:**  
   Starting from either a random or user-specified sequence, the program iteratively selects the next word based on the Markov chain, applying a backoff strategy when necessary to maintain flow.

5. **Caching:**  
   The constructed chain and starting tokens are saved to a cache file to optimize performance in subsequent runs.

---

## Running the Program

To generate text with Palimps, run the script with the appropriate arguments. For example:

```bash
python palimps.py --input path/to/text_files --output generated_text.txt --num_words 1000 --order 3
```
**Command-Line Options:**

- `--input`: Folder containing the text files for the corpus.
- `--output`: File where the generated text will be saved.
- `--num_words`: The target number of words for the generated text.
- `--order`: The order of the Markov chain (default is 3).
- `--rebuild`: Force a rebuild of the Markov chain even if a cached version exists.
- `--start`: Optionally, a starting phrase for text generation.

------------------------------------------------------------
Dependencies
------------------------------------------------------------
- **Python 3.x**
- **NLTK:** Natural Language Toolkit for tokenization and part-of-speech tagging.
- **Standard Libraries:** os, glob, random, argparse, sys, pickle

Before running the script, ensure that you have downloaded the necessary NLTK resources:

    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
