import os
import glob
import random
import argparse
import sys
import nltk
import pickle
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import defaultdict

# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

def is_grammatically_valid(sentence):
    tokens = word_tokenize(sentence)
    pos_tags = nltk.pos_tag(tokens)
    has_verb = any(tag.startswith('VB') for word, tag in pos_tags)
    if tokens.count("(") != tokens.count(")"):
        return False
    if tokens.count("\"") % 2 != 0:
        return False
    return has_verb

def build_markov_chain(sentences, order):
    chain = defaultdict(list)
    sentence_starts = []
    for sentence in sentences:
        if not is_grammatically_valid(sentence):
            continue
        tokens = word_tokenize(sentence)
        if len(tokens) < order:
            continue
        sentence_starts.append(tuple(tokens[:order]))
        for i in range(len(tokens) - order):
            print(f"Number of words on chain: {len(chain)}")
            key = tuple(tokens[i:i+order])
            next_word = tokens[i+order]
            chain[key].append(next_word)
    return chain, sentence_starts

def backoff(chain, key):
    for i in range(1, len(key)):
        reduced_key = key[i:]
        if reduced_key in chain:
            return chain[reduced_key]
    return None

def generate_text(chain, sentence_starts, order, num_words, start):
    if start:
        forced_tokens = word_tokenize(start)
        if len(forced_tokens) == order:
            forced_start = tuple(forced_tokens)
            initial_output = forced_tokens  # all tokens are used directly
        elif len(forced_tokens) < order:
            # Look for sentence_starts that begin with the forced tokens.
            candidates = [s for s in sentence_starts if s[:len(forced_tokens)] == tuple(forced_tokens)]
            if candidates:
                forced_start = random.choice(candidates)
            else:
                # Pad forced_tokens with extra words from a random sentence start.
                random_key = random.choice(sentence_starts)
                forced_start = tuple(forced_tokens + list(random_key[len(forced_tokens):]))
            initial_output = forced_tokens  # use the provided tokens as the starting output
        else:
            # If more tokens than needed, take the last `args.order` tokens as the state,
            # but include the entire starting phrase in the final output.
            forced_start = tuple(forced_tokens[-order:])
            initial_output = forced_tokens
        current_key = forced_start
    else:
        current_key = random.choice(sentence_starts)
        initial_output = list(current_key)

    # Generate text using the Markov chain.
    generated = initial_output[:]  # start with the full initial output

    while len(generated) < num_words or generated[-1] not in {'.', '!', '?'}:
        key = tuple(generated[-order:])
        candidates = chain.get(key) or backoff(chain, key)
        if not candidates:
            current_key = random.choice(sentence_starts)
            generated.extend(list(current_key))
            continue
        next_word = random.choice(candidates)
        generated.append(next_word)

    # Proper punctuation handling
    text_tokens = []
    for word in generated:
        if word in ".,!?;:":
            if text_tokens:
                text_tokens[-1] = text_tokens[-1] + word
            else:
                text_tokens.append(word)
        else:
            text_tokens.append(word)
    return ' '.join(text_tokens)

def load_corpus_from_folder(folder_path):
    corpus = ""
    txt_files = glob.glob(os.path.join(folder_path, "**/*.txt"), recursive=True)
    if not txt_files:
        print(f"No text files found in folder {folder_path}")
        sys.exit(1)
    for file_path in txt_files:
        if not os.path.isfile(file_path):
            print(f"Skipping non-file: {file_path}")
            continue
        try:
            print(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                corpus += f.read() + "\n"
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return corpus

def save_chain(chain, sentence_starts, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump({'chain': chain, 'starts': sentence_starts}, f)
    print(f"Markov chain saved to {filepath}")

def load_chain(filepath):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    print(f"Markov chain loaded from {filepath}")
    return data['chain'], data['starts']

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

    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print("Input path is not a folder.")
        sys.exit(1)

    # Path to save/load the Markov chain
    cache_path = os.path.join(args.input, f"markov_chain_order{args.order}.pkl")

    if os.path.exists(cache_path) and not args.rebuild:
        # Load from cached model
        chain, sentence_starts = load_chain(cache_path)
    else:
        # Build new model and save
        corpus_text = load_corpus_from_folder(args.input)
        sentences = sent_tokenize(corpus_text)
        print("Sentences Tokenized")
        print("Building Markov Chains")
        chain, sentence_starts = build_markov_chain(sentences, args.order)

        if not chain:
            print("No valid sentences found after preprocessing. Check your corpus.")
            sys.exit(1)
        save_chain(chain, sentence_starts, cache_path)

    generated_text = generate_text(chain, sentence_starts, args.order, args.num_words, args.start)

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(generated_text)
        print(f"Generated text of {args.num_words} words saved to {args.output}")
    except Exception as e:
        print("Error writing output file:", e)
        sys.exit(1)

if __name__ == '__main__':
    main()