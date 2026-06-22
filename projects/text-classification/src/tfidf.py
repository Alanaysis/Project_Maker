"""
TF-IDF (Term Frequency-Inverse Document Frequency) Vectorizer.

TF-IDF is a numerical statistic that reflects how important a word is to a document
in a collection or corpus. It is often used as a weighting factor in text mining.

The TF-IDF value increases proportionally to the number of times a word appears in
the document and is offset by the number of documents in the corpus that contain the
word, which helps to adjust for the fact that some words appear more frequently in general.

Formula:
    TF(t, d) = (Number of times term t appears in document d) / (Total number of terms in document d)
    IDF(t) = log(Total number of documents / Number of documents with term t in it)
    TF-IDF(t, d) = TF(t, d) * IDF(t)
"""

import math
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


class TFIDFVectorizer:
    """
    Convert a collection of raw documents to a matrix of TF-IDF features.

    This implementation provides:
    - Term Frequency (TF): How frequently a term appears in a document
    - Inverse Document Frequency (IDF): How rare a term is across all documents
    - TF-IDF: The product of TF and IDF

    Parameters
    ----------
    max_features : int or None, default=None
        Maximum number of features to keep. If None, keep all features.
    min_df : float or int, default=1
        If float, represents a proportion of documents (0.0 to 1.0).
        If int, represents absolute number of documents.
        Ignores terms that have a document frequency strictly lower than the threshold.
    max_df : float or int, default=1.0
        If float, represents a proportion of documents (0.0 to 1.0).
        If int, represents absolute number of documents.
        Ignores terms that have a document frequency strictly higher than the threshold.
    norm : 'l1', 'l2' or None, default='l2'
        Norm used to normalize term vectors. None for no normalization.
    use_idf : bool, default=True
        Enable inverse-document-frequency reweighting.
    smooth_idf : bool, default=True
        Smooth IDF weights by adding one to document frequencies, as if an extra
        document was seen containing every term in the collection exactly once.
        Prevents zero divisions.
    sublinear_tf : bool, default=False
        Apply sublinear TF scaling (replace tf with 1 + log(tf)).
    """

    def __init__(
        self,
        max_features: Optional[int] = None,
        min_df: float = 1,
        max_df: float = 1.0,
        norm: Optional[str] = "l2",
        use_idf: bool = True,
        smooth_idf: bool = True,
        sublinear_tf: bool = False,
    ):
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.norm = norm
        self.use_idf = use_idf
        self.smooth_idf = smooth_idf
        self.sublinear_tf = sublinear_tf

        # Learned attributes
        self.vocabulary_: Dict[str, int] = {}  # word -> index mapping
        self.idf_: Optional[List[float]] = None  # IDF weights
        self.feature_names_: List[str] = []  # ordered feature names

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
        # Simple preprocessing: lowercase and split on whitespace
        # Remove basic punctuation
        text = text.lower()
        for char in ".,!?;:()[]{}\"'":
            text = text.replace(char, " ")
        return text.split()

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """
        Compute term frequency for a single document.

        Parameters
        ----------
        tokens : list of str
            List of tokens from the document.

        Returns
        -------
        dict
            Mapping from term to its term frequency.
        """
        counter = Counter(tokens)
        total = len(tokens)

        if total == 0:
            return {}

        tf = {}
        for term, count in counter.items():
            frequency = count / total
            if self.sublinear_tf:
                frequency = 1 + math.log(frequency) if frequency > 0 else 0
            tf[term] = frequency

        return tf

    def _compute_idf(self, documents: List[List[str]]) -> Dict[str, float]:
        """
        Compute inverse document frequency for all terms.

        Parameters
        ----------
        documents : list of list of str
            List of tokenized documents.

        Returns
        -------
        dict
            Mapping from term to its IDF weight.
        """
        n_documents = len(documents)
        df = Counter()  # document frequency

        for doc in documents:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1

        idf = {}
        for term, freq in df.items():
            if self.smooth_idf:
                idf[term] = math.log((1 + n_documents) / (1 + freq)) + 1
            else:
                idf[term] = math.log(n_documents / freq) + 1

        return idf

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

        # Compute thresholds
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

    def fit(self, documents: List[str]) -> "TFIDFVectorizer":
        """
        Learn vocabulary and IDF weights from training documents.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        self
            Fitted vectorizer.
        """
        # Tokenize all documents
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

        # Compute IDF for valid terms
        if self.use_idf:
            idf_values = self._compute_idf(tokenized_docs)
        else:
            idf_values = {term: 1.0 for term in valid_terms}

        # Filter to valid terms only
        filtered_idf = {
            term: idf_values[term]
            for term in valid_terms
            if term in idf_values
        }

        # Sort by IDF value (descending) and apply max_features
        sorted_terms = sorted(
            filtered_idf.items(), key=lambda x: x[1], reverse=True
        )

        if self.max_features is not None:
            sorted_terms = sorted_terms[: self.max_features]

        # Build vocabulary
        self.vocabulary_ = {
            term: idx for idx, (term, _) in enumerate(sorted_terms)
        }
        self.feature_names_ = [term for term, _ in sorted_terms]
        self.idf_ = [idf for _, idf in sorted_terms]

        return self

    def transform(self, documents: List[str]) -> List[List[float]]:
        """
        Transform documents to TF-IDF feature vectors.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        list of list of float
            TF-IDF feature matrix. Each row is a document, each column is a feature.
        """
        if not self.vocabulary_:
            raise RuntimeError("Vectorizer has not been fitted. Call fit() first.")

        n_features = len(self.vocabulary_)
        result = []

        for doc in documents:
            # Tokenize
            tokens = self._tokenize(doc)

            # Compute TF
            tf = self._compute_tf(tokens)

            # Create feature vector
            vector = [0.0] * n_features

            for term, tf_value in tf.items():
                if term in self.vocabulary_:
                    idx = self.vocabulary_[term]
                    if self.use_idf:
                        vector[idx] = tf_value * self.idf_[idx]
                    else:
                        vector[idx] = tf_value

            # Normalize
            if self.norm == "l2":
                norm = math.sqrt(sum(x * x for x in vector))
                if norm > 0:
                    vector = [x / norm for x in vector]
            elif self.norm == "l1":
                norm = sum(abs(x) for x in vector)
                if norm > 0:
                    vector = [x / norm for x in vector]

            result.append(vector)

        return result

    def fit_transform(self, documents: List[str]) -> List[List[float]]:
        """
        Fit to documents, then transform them.

        Parameters
        ----------
        documents : list of str
            Raw text documents.

        Returns
        -------
        list of list of float
            TF-IDF feature matrix.
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
            "norm": self.norm,
            "use_idf": self.use_idf,
            "smooth_idf": self.smooth_idf,
            "sublinear_tf": self.sublinear_tf,
        }
