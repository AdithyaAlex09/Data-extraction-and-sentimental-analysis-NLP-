import yaml
import re
import os
import string
import syllables
import logging
import pandas as pd
from utils import setup_logging, create_directory

def load_config(filepath):
    with open(filepath, 'r') as file:
        config = yaml.safe_load(file)
    return config

def load_stopwords_from_files(filepaths):
    combined_stopwords = set()
    for filepath in filepaths:
        with open(filepath, 'r') as file:
            stopwords = file.read().splitlines()
            combined_stopwords.update(stopwords)
    return list(combined_stopwords)

def load_words(filepath):
    with open(filepath, 'r') as file:
        words = file.read().splitlines()
    return set(words)

def read_text_from_directory(directory):
    texts = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filepath.endswith('.txt'):
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    text = file.read()
                    texts.append((filename, text))
            except UnicodeDecodeError:
                logging.warning(f"Failed to decode {filepath}. Skipping file.")
    return texts


def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def count_syllables(word):
    if word.endswith('es') or word.endswith('ed'):
        word = word[:-2]
    return syllables.estimate(word) 

def syllable_count_per_word(text):
    words = tokenize(text)
    syllable_counts = {word: count_syllables(word) for word in words}
    return syllable_counts

def count_personal_pronouns(text):
    pronoun_pattern = r'\b(i|we|my|ours|us)\b'
    matches = re.findall(pronoun_pattern, text, re.IGNORECASE)
    return len(matches)

def count_complex_words(text, stopwords):
    words = tokenize(text)
    return sum(1 for word in words if count_syllables(word) > 2 and word not in stopwords)

def remove_stopwords(tokens, stopwords):
    return [word for word in tokens if word not in stopwords]

def remove_punctuation(word):
    return word.strip(string.punctuation)

def count_cleaned_words(text, stopwords):
    tokens = tokenize(text)
    tokens_no_punctuation = [remove_punctuation(word) for word in tokens]
    cleaned_tokens = remove_stopwords(tokens_no_punctuation, stopwords)
    return len(cleaned_tokens)

def calculate_scores(tokens, positive_words, negative_words):
    positive_score = sum(1 for token in tokens if token in positive_words)
    negative_score = -sum(1 for token in tokens if token in negative_words)
    return positive_score, negative_score

def calculate_polarity_score(positive_score, negative_score):
    denominator = (positive_score + negative_score) + 0.000001
    return (positive_score - negative_score) / denominator

def calculate_subjectivity_score(positive_score, negative_score, total_words):
    denominator = total_words + 0.000001
    return (positive_score + negative_score) / denominator

def calculate_fog_index(text, stopwords):
    sentences = re.split(r'\.\s*', text)  
    num_sentences = max(len(sentences), 1)
    
    words = tokenize(text)
    num_words = max(len(words), 1)
    
    num_complex_words = count_complex_words(text, stopwords)
    
    average_sentence_length = num_words / num_sentences
    percentage_complex_words = num_complex_words / num_words
    fog_index = 0.4 * (average_sentence_length + percentage_complex_words)
    
    average_words_per_sentence = num_words / num_sentences
    
    return average_sentence_length, percentage_complex_words, fog_index, average_words_per_sentence

def calculate_average_word_length(text):
    words = tokenize(text)
    if len(words) == 0:
        return 0 
    total_characters = sum(len(word) for word in words)
    return total_characters / len(words)

def main():
    config = load_config('config/config.yaml')
    
    stopwords_files = config['stopwords_files']
    positive_words_file = config.get('master_dictionary', {}).get('positive_words')
    negative_words_file = config.get('master_dictionary', {}).get('negative_words')
    syllable_words_directory = config.get('syllables_directory', {}).get('directory')
    log_directory = config.get('analysislog_file', {}).get('log_directory')
    log_file = config.get('analysislog_file', {}).get('log_file')
    input_directory = config.get('scraping', {}).get('output_directory')
    submission_file = config.get('submission_directory', {}).get('finaloutput_directory')  
    
    create_directory(syllable_words_directory)
    create_directory(log_directory)
    setup_logging(log_file)
    
    combined_stopwords = load_stopwords_from_files(stopwords_files)
    positive_words = load_words(positive_words_file)
    negative_words = load_words(negative_words_file)
    
    texts = read_text_from_directory(input_directory)

    df = pd.read_excel(submission_file)
    
    for filename, text in texts:
        tokens = tokenize(text)
        cleaned_tokens = remove_stopwords(tokens, combined_stopwords)
        
        word_count = count_cleaned_words(text, combined_stopwords)
        
        syllable_counts = syllable_count_per_word(text)
        total_syllables = sum(syllable_counts.values())
        
        syllable_counts_path = os.path.join(syllable_words_directory, f'syllable_counts_{os.path.splitext(filename)[0]}.txt')
        with open(syllable_counts_path, 'w') as file:
            for word, count in syllable_counts.items():
                file.write(f"{word}: {count}\n")
        
        pronoun_count = count_personal_pronouns(text)
        
        positive_score, negative_score = calculate_scores(cleaned_tokens, positive_words, negative_words)
        
        polarity_score = calculate_polarity_score(positive_score, negative_score)
        
        total_words = len(cleaned_tokens)
        subjectivity_score = calculate_subjectivity_score(positive_score, negative_score, total_words)
        
        avg_sentence_length, perc_complex_words, fog_index, avg_words_per_sentence = calculate_fog_index(text, combined_stopwords)
        
        avg_word_length = calculate_average_word_length(text)
        
        logging.info(f"File: {filename}")
        logging.info(f"Word Count: {word_count}")
        logging.info(f"Positive Score: {positive_score}")
        logging.info(f"Negative Score: {negative_score}")
        logging.info(f"Polarity Score: {polarity_score:.4f}")
        logging.info(f"Subjectivity Score: {subjectivity_score:.4f}")
        logging.info(f"Average Sentence Length: {avg_sentence_length:.2f}")
        logging.info(f"Percentage of Complex Words: {perc_complex_words:.4f}")
        logging.info(f"Fog Index: {fog_index:.2f}")
        logging.info(f"Average Number of Words Per Sentence: {avg_words_per_sentence:.2f}")
        logging.info(f"Complex Word Count: {count_complex_words(text, combined_stopwords)}")
        logging.info(f"Total Syllables: {total_syllables}")
        logging.info(f"Personal Pronouns Count: {pronoun_count}")
        logging.info(f"Average Word Length: {avg_word_length:.2f}")
        
        url_id = os.path.splitext(filename)[0]
        if url_id in df['URL_ID'].values:
            df.loc[df['URL_ID'] == url_id, 'WORD COUNT'] = word_count
            df.loc[df['URL_ID'] == url_id, 'POSITIVE SCORE'] = positive_score
            df.loc[df['URL_ID'] == url_id, 'NEGATIVE SCORE'] = negative_score
            df.loc[df['URL_ID'] == url_id, 'POLARITY SCORE'] = polarity_score
            df.loc[df['URL_ID'] == url_id, 'SUBJECTIVITY SCORE'] = subjectivity_score
            df.loc[df['URL_ID'] == url_id, 'AVG SENTENCE LENGTH'] = avg_sentence_length
            df.loc[df['URL_ID'] == url_id, 'PERCENTAGE OF COMPLEX WORDS'] = perc_complex_words
            df.loc[df['URL_ID'] == url_id, 'FOG INDEX'] = fog_index
            df.loc[df['URL_ID'] == url_id, 'AVG NUMBER OF WORDS PER SENTENCE'] = avg_words_per_sentence
            df.loc[df['URL_ID'] == url_id, 'COMPLEX WORD COUNT'] = count_complex_words(text, combined_stopwords)
            df.loc[df['URL_ID'] == url_id, 'SYLLABLE PER WORD'] = total_syllables
            df.loc[df['URL_ID'] == url_id, 'PERSONAL PRONOUNS'] = pronoun_count
            df.loc[df['URL_ID'] == url_id, 'AVG WORD LENGTH'] = avg_word_length
    
    df.to_excel(submission_file, index=False)

if __name__ == "__main__":
    main()



















