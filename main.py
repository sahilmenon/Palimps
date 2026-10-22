import os
import re
import glob
import random
import argparse
import sys
import nltk
import pickle
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import defaultdict

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

MAX_GENERATION_ITERS = 10000
NOVELTY_NGRAM_SIZE = 7


def is_grammatically_valid(sentence):
    tokens = word_tokenize(sentence)
    pos_tags = nltk.pos_tag(tokens)
    has_verb = any(tag.startswith('VB') for _, tag in pos_tags)
    if tokens.count("(") != tokens.count(")"):
        return False
    if tokens.count('"') % 2 != 0:
        return False
    return has_verb


def build_source_ngrams(sentences):
    """Build a set of word n-grams from source sentences for novelty checking."""
    ngrams = set()
    for sentence in sentences:
        words = sentence.lower().split()
        for i in range(len(words) - NOVELTY_NGRAM_SIZE + 1):
            ngrams.add(tuple(words[i:i + NOVELTY_NGRAM_SIZE]))
    return ngrams


def is_novel(text, source_ngrams):
    """Return False if any n-gram from text appears verbatim in the source corpus."""
    words = text.lower().split()
    if len(words) < NOVELTY_NGRAM_SIZE:
        return True
    for i in range(len(words) - NOVELTY_NGRAM_SIZE + 1):
        if tuple(words[i:i + NOVELTY_NGRAM_SIZE]) in source_ngrams:
            return False
    return True


def build_markov_chain(sentences, order):
    chain = defaultdict(list)
    sentence_starts = []
    valid_sentences = []
    for sentence in sentences:
        if not is_grammatically_valid(sentence):
            continue
        tokens = word_tokenize(sentence)
        if len(tokens) < order:
            continue
        valid_sentences.append(sentence)
        sentence_starts.append(tuple(tokens[:order]))
        for i in range(len(tokens) - order):
            key = tuple(tokens[i:i + order])
            chain[key].append(tokens[i + order])
    return chain, sentence_starts, valid_sentences


def backoff(chain, key):
    for i in range(1, len(key)):
        reduced_key = key[i:]
        if reduced_key in chain:
            return chain[reduced_key]
    return None


def detokenize(tokens):
    """Reconstruct readable text from NLTK word tokens."""
    text = ' '.join(tokens)
    # Contractions and possessives: do n't -> don't, it 's -> it's
    text = re.sub(r" (n't|'s|'re|'ve|'ll|'d|'m)\b", r"\1", text)
    # No space before sentence-ending and mid-sentence punctuation
    text = re.sub(r' ([.,!?;:\)\]}-])', r'\1', text)
    # No space after opening brackets
    text = re.sub(r'([\(\[{]) ', r'\1', text)
    # NLTK backtick-style quotes: `` word '' -> "word"
    text = re.sub(r"`` (.*?) ''", r'"\1"', text)
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def generate_text(chain, sentence_starts, order, num_words, start, source_ngrams=None):
    if start:
        forced_tokens = word_tokenize(start)
        if len(forced_tokens) == order:
            current_key = tuple(forced_tokens)
            initial_output = forced_tokens
        elif len(forced_tokens) < order:
            candidates = [s for s in sentence_starts if s[:len(forced_tokens)] == tuple(forced_tokens)]
            if candidates:
                current_key = random.choice(candidates)
            else:
                random_key = random.choice(sentence_starts)
                current_key = tuple(forced_tokens + list(random_key[len(forced_tokens):]))
            initial_output = forced_tokens
        else:
            current_key = tuple(forced_tokens[-order:])
            initial_output = forced_tokens
    else:
        current_key = random.choice(sentence_starts)
        initial_output = list(current_key)

    generated = initial_output[:]
    iters = 0

    while len(generated) < num_words or generated[-1] not in {'.', '!', '?'}:
        iters += 1
        if iters > MAX_GENERATION_ITERS:
            if generated[-1] not in {'.', '!', '?'}:
                generated.append('.')
            print(f"Warning: hit iteration limit ({MAX_GENERATION_ITERS}); output may be shorter than requested.")
            break

        key = tuple(generated[-order:])
        candidates = chain.get(key) or backoff(chain, key)
        if not candidates:
            seed = random.choice(sentence_starts)
            generated.extend(list(seed))
            continue
        generated.append(random.choice(candidates))

    text = detokenize(generated)

    if source_ngrams and not is_novel(text, source_ngrams):
        print("Warning: generated text contains passages closely matching the source corpus.")

    return text


def load_corpus_from_folder(folder_path):
    corpus = ""
    txt_files = glob.glob(os.path.join(folder_path, "**/*.txt"), recursive=True)
    if not txt_files:
        print(f"No text files found in folder {folder_path}")
        sys.exit(1)
    for file_path in txt_files:
        if not os.path.isfile(file_path):
            continue
        try:
            print(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                corpus += f.read() + "\n"
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return corpus


def save_chain(chain, sentence_starts, valid_sentences, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump({'chain': chain, 'starts': sentence_starts, 'sentences': valid_sentences}, f)
    print(f"Markov chain saved to {filepath}")


def load_chain(filepath):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    print(f"Markov chain loaded from {filepath}")
    return data['chain'], data['starts'], data.get('sentences', [])


def main():
    parser = argparse.ArgumentParser(
        description="Generate text using a grammar-preprocessed Markov chain from a folder of text files."
    )
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the input folder containing text files.")
    parser.add_argument("--output", type=str, default="generated_text.txt",
                        help="Output file for the generated text.")
    parser.add_argument("--num_words", type=int, default=1000,
                        help="Number of words to generate (default: 1000).")
    parser.add_argument("--order", type=int, default=3,
                        help="Order of the Markov chain (recommended: 3 for large corpora).")
    parser.add_argument("--rebuild", action='store_true',
                        help="Force rebuild the Markov chain even if cache exists.")
    parser.add_argument("--start", type=str,
                        help="Optional starting phrase for the generated text.")
    parser.add_argument("--no-novelty-check", action='store_true',
                        help="Disable novelty checking (faster, but may echo source text).")

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print("Input path is not a folder.")
        sys.exit(1)

    cache_path = os.path.join(args.input, f"markov_chain_order{args.order}.pkl")

    if os.path.exists(cache_path) and not args.rebuild:
        chain, sentence_starts, valid_sentences = load_chain(cache_path)
        if not args.no_novelty_check and not valid_sentences:
            print("Note: cached model predates novelty checking; run with --rebuild to enable it.")
    else:
        corpus_text = load_corpus_from_folder(args.input)
        sentences = sent_tokenize(corpus_text)
        print("Sentences tokenized")
        print("Building Markov chain...")
        chain, sentence_starts, valid_sentences = build_markov_chain(sentences, args.order)

        if not chain:
            print("No valid sentences found after preprocessing. Check your corpus.")
            sys.exit(1)
        save_chain(chain, sentence_starts, valid_sentences, cache_path)

    source_ngrams = None
    if not args.no_novelty_check and valid_sentences:
        source_ngrams = build_source_ngrams(valid_sentences)

    generated_text = generate_text(
        chain, sentence_starts, args.order, args.num_words, args.start, source_ngrams
    )

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(generated_text)
        print(f"Generated text of {args.num_words} words saved to {args.output}")
    except Exception as e:
        print("Error writing output file:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
