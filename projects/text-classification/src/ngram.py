"""
N-gram Feature Extractor.

N-grams are contiguous sequences of n items from a given text or speech.
They are used to capture local word order information that Bag of Words misses.

Types:
- Unigram (n=1): Single words ["the", "cat", "sat"]
- Bigram (n=2): Pairs of words ["the cat", "cat sat", "sat on"]
- Trigram (n=3): Triples of words ["the cat sat", "cat sat on"]

Example:
    Text: "the cat sat on the mat"
    Bigrams: ["the cat", "cat sat", "sat on", "on the", "the mat"]
"""

from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


class NGramVectorizer:
    """
    Convert a collection of text documents to a matrix of N-gram counts.

    This implementation supports:
    - Character-level N-grams
    - Word-level N-grams
    - Configurable N range (e.g., unigrams + bigrams)

    Parameters
    ----------
    ngram_range : tuple of (int, int), default=(1, 1)
        The lower and upper boundary of the range of n-values for different
        n-grams. (1, 1) means only unigrams, (1, 2) means unigrams + bigrams.
    max_features : int or None, default=None
        Maximum number of features to keep.
    min_df : float or int, default=1
        Minimum document frequency threshold.
    max_df : float or int, default=1.0
        Maximum document frequency threshold.
    analyzer : str, default='word'
        Whether the feature should be made of word n-grams or character n-grams.
        Options: 'word', 'char'.
    """

    def __init__(
        self,
        ngram_range: Tuple[int, int] = (1, 1),
        max_features: Optional[int] = None,
        min_df: float = 1,
        max_df: float = 1.0,
        analyzer: str = "word",
    ):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.analyzer = analyzer

        # Learned attributes
        self.vocabulary_: Dict[str, int] = {}
        self.feature_names_: List[str] = []

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenizer that splits on whitespace and converts to lowercase.

        Parameters
        ----------
        text : str
            Input text to tokenize.

        Returns
        -------
        list of str
            List of tokens.
        """
        text = text.lower()
        for char in ".,!?;:()[]{}\"'":
            text = text.replace(char, " ")
        return text.split()

    def _generate_ngrams(self, tokens: List[str]) -> List[str]:
        """
        Generate N-grams from a list of tokens.

        Parameters
        ----------
        tokens : list of str
            List of tokens (words or characters).

        Returns
        -------
        list of str
            List of N-gram strings.
        """
        ngrams = []
        min_n, max_n = self.ngram_range

        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i : i + n])
                ngrams.append(ngram)

        return ngrams

    def _generate_char_ngrams(self, text: str) -> List[str]:
        """
        Generate character-level N-grams from text.

        Parameters
        ----------
        text : str
            Input text.

        Returns
        -------
        list of str
            List of character N-gram strings.
        """
        text = text.lower()
        ngrams = []
        min_n, max_n = self.ngram_range

        for n in range(min_n, max_n + 1):
            for i in range(len(text) - n + 1):
                ngram = text[i : i + n]
                ngrams.append(ngram)

        return ngrams

    def _apply_df_filter(
        self, df: Dict[str, int], n_documents: int
    ) -> Set[str]:
        """
        Filter terms based on document frequency thresholds.

        Parameters
        ----------
        df : dict
            Document frequency for each term.
        n_documents : int
            Total number of documents.

        Returns
        -------
        set of str
            Set of terms that pass the filter.
        """
        valid_terms = set()

        if isinstance(self.min_df, float):
            min_threshold = self.min_df * n_documents
        else:
            min_threshold = self.min_df

        if isinstance(self.max_df, float):
            max_threshold = self.max_df * n_documents
        else:
            max_threshold = self.max_df

        for term, freq in df.items():
            if freq >= min_threshold and freq <= max_threshold:
                valid_terms.add(term)

        return valid_terms

    def fit(self, documents: List[str]) -> "NGramVectorizer":
        """
        Learn vocabulary from training documents.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        self
            Fitted vectorizer.
        """
        n_documents = len(documents)

        # Generate N-grams for each document
        doc_ngrams = []
        for doc in documents:
            if self.analyzer == "char":
                ngrams = self._generate_char_ngrams(doc)
            else:
                tokens = self._tokenize(doc)
                ngrams = self._generate_ngrams(tokens)
            doc_ngrams.append(ngrams)

        # Compute document frequency
        df = Counter()
        for ngrams in doc_ngrams:
            unique_ngrams = set(ngrams)
            for ngram in unique_ngrams:
                df[ngram] += 1

        # Apply document frequency filter
        valid_terms = self._apply_df_filter(df, n_documents)

        # Sort by document frequency (descending) and apply max_features
        sorted_terms = sorted(
            [(term, df[term]) for term in valid_terms],
            key=lambda x: x[1],
            reverse=True,
        )

        if self.max_features is not None:
            sorted_terms = sorted_terms[: self.max_features]

        # Build vocabulary
        self.vocabulary_ = {
            term: idx for idx, (term, _) in enumerate(sorted_terms)
        }
        self.feature_names_ = [term for term, _ in sorted_terms]

        return self

    def transform(self, documents: List[str]) -> List[List[int]]:
        """
        Transform documents to N-gram count vectors.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        list of list of int
            N-gram count matrix.
        """
        if not self.vocabulary_:
            raise RuntimeError("Vectorizer has not been fitted. Call fit() first.")

        n_features = len(self.vocabulary_)
        result = []

        for doc in documents:
            if self.analyzer == "char":
                ngrams = self._generate_char_ngrams(doc)
            else:
                tokens = self._tokenize(doc)
                ngrams = self._generate_ngrams(tokens)

            counter = Counter(ngrams)

            # Create feature vector
            vector = [0] * n_features
            for ngram, count in counter.items():
                if ngram in self.vocabulary_:
                    idx = self.vocabulary_[ngram]
                    vector[idx] = count

            result.append(vector)

        return result

    def fit_transform(self, documents: List[str]) -> List[List[int]]:
        """
        Fit to documents, then transform them.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        list of list of int
            N-gram count matrix.
        """
        return self.fit(documents).transform(documents)

    def get_feature_names(self) -> List[str]:
        """
        Get feature names (N-gram strings).

        Returns
        -------
        list of str
            Feature names ordered by index.
        """
        return self.feature_names_

    def get_params(self) -> Dict:
        """
        Get parameters of the vectorizer.

        Returns
        -------
        dict
            Parameter names mapped to their values.
        """
        return {
            "ngram_range": self.ngram_range,
            "max_features": self.max_features,
            "min_df": self.min_df,
            "max_df": self.max_df,
            "analyzer": self.analyzer,
        }
