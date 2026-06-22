"""
Text Classifier - High-level text classification pipeline.

This module provides a convenient interface that combines TF-IDF vectorization
and Naive Bayes classification into a single pipeline for text classification.

Usage:
    classifier = TextClassifier()
    classifier.fit(texts, labels)
    predictions = classifier.predict(new_texts)
"""

from typing import Dict, List, Optional, Tuple

from .tfidf import TFIDFVectorizer
from .naive_bayes import NaiveBayesClassifier


class TextClassifier:
    """
    High-level text classification pipeline combining TF-IDF and Naive Bayes.

    This class provides a simple interface for text classification:
    1. Text preprocessing and tokenization (via TFIDFVectorizer)
    2. Feature extraction (TF-IDF)
    3. Classification (Naive Bayes)

    Parameters
    ----------
    max_features : int or None, default=None
        Maximum number of TF-IDF features to keep.
    alpha : float, default=1.0
        Smoothing parameter for Naive Bayes.
    norm : 'l1', 'l2' or None, default='l2'
        Norm used to normalize TF-IDF vectors.
    use_idf : bool, default=True
        Enable IDF reweighting in TF-IDF.
    sublinear_tf : bool, default=False
        Apply sublinear TF scaling.
    """

    def __init__(
        self,
        max_features: Optional[int] = None,
        alpha: float = 1.0,
        norm: Optional[str] = "l2",
        use_idf: bool = True,
        sublinear_tf: bool = False,
    ):
        self.max_features = max_features
        self.alpha = alpha
        self.norm = norm
        self.use_idf = use_idf
        self.sublinear_tf = sublinear_tf

        # Initialize components
        self.vectorizer = TFIDFVectorizer(
            max_features=max_features,
            norm=norm,
            use_idf=use_idf,
            sublinear_tf=sublinear_tf,
        )
        self.classifier = NaiveBayesClassifier(alpha=alpha, model_type="multinomial")

        # State
        self.is_fitted = False

    def fit(self, texts: List[str], labels: List[str]) -> "TextClassifier":
        """
        Fit the text classifier on training data.

        Parameters
        ----------
        texts : list of str
            Raw text documents.
        labels : list of str
            Target class labels.

        Returns
        -------
        self
            Fitted classifier.

        Raises
        ------
        ValueError
            If texts and labels have different lengths.
        """
        if len(texts) != len(labels):
            raise ValueError(
                f"texts and labels must have the same length, "
                f"got {len(texts)} and {len(labels)}"
            )

        # Fit and transform texts to TF-IDF features
        X = self.vectorizer.fit_transform(texts)

        # Fit Naive Bayes classifier
        self.classifier.fit(X, labels)
        self.is_fitted = True

        return self

    def predict(self, texts: List[str]) -> List[str]:
        """
        Predict class labels for the given texts.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of str
            Predicted class labels.

        Raises
        ------
        RuntimeError
            If the classifier has not been fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        # Transform texts to TF-IDF features
        X = self.vectorizer.transform(texts)

        # Predict
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Return probability estimates for each class.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of dict
            Probability of each class for each text.

        Raises
        ------
        RuntimeError
            If the classifier has not been fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        # Transform texts to TF-IDF features
        X = self.vectorizer.transform(texts)

        # Get probabilities
        return self.classifier.predict_proba(X)

    def score(self, texts: List[str], labels: List[str]) -> float:
        """
        Return the mean accuracy on the given test data and labels.

        Parameters
        ----------
        texts : list of str
            Raw text documents.
        labels : list of str
            True labels.

        Returns
        -------
        float
            Mean accuracy.
        """
        predictions = self.predict(texts)
        correct = sum(1 for pred, true in zip(predictions, labels) if pred == true)
        return correct / len(labels)

    def get_top_features(self, n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get top features (words) for each class.

        Parameters
        ----------
        n : int, default=10
            Number of top features to return per class.

        Returns
        -------
        dict
            Mapping from class label to list of (feature, importance) tuples.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        feature_names = self.vectorizer.get_feature_names()
        top_features = {}

        for cls in self.classifier.classes_:
            # Get log probabilities for this class
            log_probs = self.classifier.feature_log_prob_[cls]

            # Create (feature, probability) pairs
            feature_probs = [
                (feature_names[i], log_probs[i])
                for i in range(len(feature_names))
            ]

            # Sort by probability (descending)
            feature_probs.sort(key=lambda x: x[1], reverse=True)

            # Take top n
            top_features[cls] = feature_probs[:n]

        return top_features

    def get_params(self) -> Dict:
        """
        Get parameters of the classifier pipeline.

        Returns
        -------
        dict
            Parameter names mapped to their values.
        """
        return {
            "max_features": self.max_features,
            "alpha": self.alpha,
            "norm": self.norm,
            "use_idf": self.use_idf,
            "sublinear_tf": self.sublinear_tf,
        }
