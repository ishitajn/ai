import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# It's good practice to check for NLTK data and download if necessary.
def download_nltk_resources():
    """Downloads all necessary NLTK resources."""
    resources = {
        "corpora/stopwords": "stopwords",
        "tokenizers/punkt": "punkt",
        "corpora/wordnet": "wordnet",
        "tokenizers/punkt_tab": "punkt_tab",
        "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger"
    }
    for path, resource_name in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"NLTK resource '{resource_name}' not found. Downloading...")
            nltk.download(resource_name)

download_nltk_resources()


def preprocess_text(text):
    """
    Cleans and preprocesses text by:
    - Lowercasing
    - Removing punctuation and special characters
    - Tokenizing
    - Removing stopwords
    - Lemmatizing
    """
    if not isinstance(text, str):
        return ""

    # Lowercase the text
    text = text.lower()

    # Remove punctuation and special characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)

    # Tokenize the text
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]

    # Lemmatize the tokens
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]

    return " ".join(lemmatized_tokens)
