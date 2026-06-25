"""
Bag of Words (BoW) Vectorizer.

Bag of Words is a text representation method that describes the occurrence of words
within a document. It involves two things:
1. A vocabulary of known words
2. A measure of the presence of known words

It is called a "bag" of words because the order of words is discarded, and only
the frequency of each word is considered.

Example:
    Document 1: "the cat sat on the mat"
    Document 2: "the dog sat on the log"

    Vocabulary: [cat, dog, log, mat, on, sat, the]

    Document 1 vector: [1, 0, 0, 1, 1, 1, 2]
    Document 2 vector: [0, 1, 1, 0, 1, 1, 2]
"""

from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


class BagOfWordsVectorizer:
    """
    Convert a collection of text documents to a matrix of word counts.

    This implementation provides:
    - Word counting (binary or frequency-based)
    - Vocabulary building with frequency thresholds
    - Feature name mapping

    Parameters
    ----------
    max_features : int or None, default=None
        Maximum number of features to keep. If None, keep all features.
    min_df : float or int, default=1
        Minimum document frequency threshold.
    max_df : float or int, default=1.0
        Maximum document frequency threshold.
    binary : bool, default=False
        If True, all non-zero counts are set to 1.
    """

    def __init__(
        self,
        max_features: Optional[int] = None,
        min_df: float = 1,
        max_df: float = 1.0,
        binary: bool = False,
    ):
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.binary = binary

        # Learned attributes
        self.vocabulary_: Dict[str, int] = {}
        self.feature_names_: List[str] = []
        self._idf_values: Dict[str, float] = {}

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

    def fit(self, documents: List[str]) -> "BagOfWordsVectorizer":
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
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        n_documents = len(tokenized_docs)

        # Compute document frequency
        df = Counter()
        for doc in tokenized_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1

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
        Transform documents to Bag of Words feature vectors.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        list of list of int
            BoW feature matrix. Each row is a document, each column is a feature.
        """
        if not self.vocabulary_:
            raise RuntimeError("Vectorizer has not been fitted. Call fit() first.")

        n_features = len(self.vocabulary_)
        result = []

        for doc in documents:
            tokens = self._tokenize(doc)
            counter = Counter(tokens)

            # Create feature vector
            vector = [0] * n_features
            for term, count in counter.items():
                if term in self.vocabulary_:
                    idx = self.vocabulary_[term]
                    vector[idx] = 1 if self.binary else count

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
            BoW feature matrix.
        """
        return self.fit(documents).transform(documents)

    def get_feature_names(self) -> List[str]:
        """
        Get feature names (vocabulary terms).

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
            "max_features": self.max_features,
            "min_df": self.min_df,
            "max_df": self.max_df,
            "binary": self.binary,
        }
