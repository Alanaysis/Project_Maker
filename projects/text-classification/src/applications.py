"""
Real-world Text Classification Applications.

This module provides ready-to-use applications for common text classification tasks:
- Sentiment Analysis: Classify text as positive/negative
- News Classification: Categorize news articles
- Spam Detection: Detect spam messages
"""

from typing import Dict, List, Optional, Tuple

from .tfidf import TFIDFVectorizer
from .naive_bayes import NaiveBayesClassifier
from .logistic_regression import LogisticRegressionClassifier
from .svm_classifier import SVMClassifier
from .evaluation import accuracy, precision, recall, f1_score, confusion_matrix, classification_report


class SentimentAnalyzer:
    """
    Sentiment Analysis classifier.

    Classifies text as positive or negative sentiment.

    Parameters
    ----------
    classifier_type : str, default='naive_bayes'
        Type of classifier to use: 'naive_bayes', 'logistic_regression', 'svm'.
    max_features : int, default=5000
        Maximum number of TF-IDF features.
    """

    def __init__(
        self,
        classifier_type: str = "naive_bayes",
        max_features: int = 5000,
    ):
        self.classifier_type = classifier_type
        self.max_features = max_features

        # Initialize vectorizer
        self.vectorizer = TFIDFVectorizer(
            max_features=max_features,
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )

        # Initialize classifier
        if classifier_type == "naive_bayes":
            self.classifier = NaiveBayesClassifier(alpha=1.0, model_type="multinomial")
        elif classifier_type == "logistic_regression":
            self.classifier = LogisticRegressionClassifier(learning_rate=0.1, max_iter=500)
        elif classifier_type == "svm":
            self.classifier = SVMClassifier(C=1.0, max_iter=500)
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")

        self.is_fitted = False

    def fit(self, texts: List[str], labels: List[str]) -> "SentimentAnalyzer":
        """
        Fit the sentiment analyzer on training data.

        Parameters
        ----------
        texts : list of str
            Raw text documents.
        labels : list of str
            Sentiment labels (e.g., 'positive', 'negative').

        Returns
        -------
        self
            Fitted analyzer.
        """
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str]) -> List[str]:
        """
        Predict sentiment for given texts.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of str
            Predicted sentiment labels.
        """
        if not self.is_fitted:
            raise RuntimeError("Analyzer has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Predict sentiment probabilities.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of dict
            Probability of each sentiment class.
        """
        if not self.is_fitted:
            raise RuntimeError("Analyzer has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(X)

    def evaluate(self, texts: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Evaluate the analyzer on test data.

        Parameters
        ----------
        texts : list of str
            Test text documents.
        labels : list of str
            True sentiment labels.

        Returns
        -------
        dict
            Evaluation metrics.
        """
        predictions = self.predict(texts)
        return {
            "accuracy": accuracy(labels, predictions),
            "precision": precision(labels, predictions),
            "recall": recall(labels, predictions),
            "f1": f1_score(labels, predictions),
        }


class NewsClassifier:
    """
    News Article Classifier.

    Classifies news articles into categories like sports, politics, technology, etc.

    Parameters
    ----------
    classifier_type : str, default='logistic_regression'
        Type of classifier to use.
    max_features : int, default=10000
        Maximum number of TF-IDF features.
    """

    def __init__(
        self,
        classifier_type: str = "logistic_regression",
        max_features: int = 10000,
    ):
        self.classifier_type = classifier_type
        self.max_features = max_features

        # Initialize vectorizer with bigrams
        self.vectorizer = TFIDFVectorizer(
            max_features=max_features,
            min_df=3,
            max_df=0.9,
            sublinear_tf=True,
        )

        # Initialize classifier
        if classifier_type == "naive_bayes":
            self.classifier = NaiveBayesClassifier(alpha=0.5, model_type="multinomial")
        elif classifier_type == "logistic_regression":
            self.classifier = LogisticRegressionClassifier(learning_rate=0.05, max_iter=1000)
        elif classifier_type == "svm":
            self.classifier = SVMClassifier(C=0.5, max_iter=1000)
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")

        self.is_fitted = False

    def fit(self, texts: List[str], labels: List[str]) -> "NewsClassifier":
        """
        Fit the news classifier on training data.

        Parameters
        ----------
        texts : list of str
            Raw text documents.
        labels : list of str
            Category labels (e.g., 'sports', 'politics', 'technology').

        Returns
        -------
        self
            Fitted classifier.
        """
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str]) -> List[str]:
        """
        Predict category for given texts.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of str
            Predicted category labels.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Predict category probabilities.

        Parameters
        ----------
        texts : list of str
            Raw text documents.

        Returns
        -------
        list of dict
            Probability of each category.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(X)

    def evaluate(self, texts: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Evaluate the classifier on test data.

        Parameters
        ----------
        texts : list of str
            Test text documents.
        labels : list of str
            True category labels.

        Returns
        -------
        dict
            Evaluation metrics.
        """
        predictions = self.predict(texts)
        return {
            "accuracy": accuracy(labels, predictions),
            "precision_macro": precision(labels, predictions, "macro"),
            "recall_macro": recall(labels, predictions, "macro"),
            "f1_macro": f1_score(labels, predictions, "macro"),
        }

    def get_top_features_per_class(self, n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get top features (words) for each category.

        Parameters
        ----------
        n : int, default=10
            Number of top features to return per category.

        Returns
        -------
        dict
            Mapping from category to list of (feature, importance) tuples.
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        feature_names = self.vectorizer.get_feature_names()
        top_features = {}

        if hasattr(self.classifier, 'classes_') and hasattr(self.classifier, 'weights_'):
            for cls in self.classifier.classes_:
                if cls in self.classifier.weights_:
                    weights = self.classifier.weights_[cls]
                    feature_weights = [(feature_names[i], abs(weights[i])) for i in range(len(feature_names))]
                    feature_weights.sort(key=lambda x: x[1], reverse=True)
                    top_features[cls] = feature_weights[:n]

        return top_features


class SpamDetector:
    """
    Spam Detection classifier.

    Classifies messages as spam or not spam (ham).

    Parameters
    ----------
    classifier_type : str, default='naive_bayes'
        Type of classifier to use.
    max_features : int, default=3000
        Maximum number of TF-IDF features.
    """

    def __init__(
        self,
        classifier_type: str = "naive_bayes",
        max_features: int = 3000,
    ):
        self.classifier_type = classifier_type
        self.max_features = max_features

        # Initialize vectorizer
        self.vectorizer = TFIDFVectorizer(
            max_features=max_features,
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )

        # Initialize classifier
        if classifier_type == "naive_bayes":
            self.classifier = NaiveBayesClassifier(alpha=1.0, model_type="multinomial")
        elif classifier_type == "logistic_regression":
            self.classifier = LogisticRegressionClassifier(learning_rate=0.1, max_iter=500)
        elif classifier_type == "svm":
            self.classifier = SVMClassifier(C=1.0, max_iter=500)
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")

        self.is_fitted = False

    def fit(self, texts: List[str], labels: List[str]) -> "SpamDetector":
        """
        Fit the spam detector on training data.

        Parameters
        ----------
        texts : list of str
            Raw text messages.
        labels : list of str
            Labels ('spam' or 'ham').

        Returns
        -------
        self
            Fitted detector.
        """
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str]) -> List[str]:
        """
        Predict spam/ham for given texts.

        Parameters
        ----------
        texts : list of str
            Raw text messages.

        Returns
        -------
        list of str
            Predicted labels ('spam' or 'ham').
        """
        if not self.is_fitted:
            raise RuntimeError("Detector has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Predict spam probabilities.

        Parameters
        ----------
        texts : list of str
            Raw text messages.

        Returns
        -------
        list of dict
            Probability of spam/ham.
        """
        if not self.is_fitted:
            raise RuntimeError("Detector has not been fitted. Call fit() first.")

        X = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(X)

    def evaluate(self, texts: List[str], labels: List[str]) -> Dict[str, float]:
        """
        Evaluate the detector on test data.

        Parameters
        ----------
        texts : list of str
            Test text messages.
        labels : list of str
            True labels.

        Returns
        -------
        dict
            Evaluation metrics.
        """
        predictions = self.predict(texts)
        return {
            "accuracy": accuracy(labels, predictions),
            "precision": precision(labels, predictions),
            "recall": recall(labels, predictions),
            "f1": f1_score(labels, predictions),
        }


def create_sample_sentiment_data() -> Tuple[List[str], List[str]]:
    """
    Create sample sentiment analysis data.

    Returns
    -------
    tuple of (list of str, list of str)
        Texts and labels.
    """
    texts = [
        "I love this movie, it is absolutely wonderful!",
        "This is the best film I have ever seen.",
        "Great acting and amazing storyline.",
        "Highly recommended, a masterpiece!",
        "The cinematography was stunning and beautiful.",
        "I hate this movie, it is terrible.",
        "Worst film ever, complete waste of time.",
        "Awful acting and boring storyline.",
        "Do not watch this, it is horrible.",
        "The plot was confusing and the ending was disappointing.",
    ]
    labels = [
        "positive", "positive", "positive", "positive", "positive",
        "negative", "negative", "negative", "negative", "negative",
    ]
    return texts, labels


def create_sample_news_data() -> Tuple[List[str], List[str]]:
    """
    Create sample news classification data.

    Returns
    -------
    tuple of (list of str, list of str)
        Texts and labels.
    """
    texts = [
        "The team won the championship game in overtime.",
        "The player scored a hat trick in the match.",
        "The coach announced his retirement after the season.",
        "The new smartphone features an advanced camera system.",
        "The company released a major software update today.",
        "Artificial intelligence is transforming the tech industry.",
        "The election results were announced after a close race.",
        "The president signed a new economic policy into law.",
        "Parliament debated the proposed healthcare reform.",
        "The stock market reached an all-time high today.",
        "The central bank announced a change in interest rates.",
        "The trade agreement between countries was finalized.",
    ]
    labels = [
        "sports", "sports", "sports",
        "technology", "technology", "technology",
        "politics", "politics", "politics",
        "finance", "finance", "finance",
    ]
    return texts, labels


def create_sample_spam_data() -> Tuple[List[str], List[str]]:
    """
    Create sample spam detection data.

    Returns
    -------
    tuple of (list of str, list of str)
        Texts and labels.
    """
    texts = [
        "Congratulations! You have won a free iPhone. Click here to claim now!",
        "URGENT: Your account has been compromised. Verify your password immediately.",
        "Make money fast! Work from home and earn thousands per week.",
        "Free trial! Limited time offer. Act now before it expires.",
        "You are selected for a special prize. Send your details to claim.",
        "Hi, are we still meeting for lunch tomorrow?",
        "Please find attached the report for the quarterly review.",
        "The project deadline has been extended to next Friday.",
        "Can you send me the meeting notes from today's call?",
        "Happy birthday! Hope you have a wonderful day.",
    ]
    labels = [
        "spam", "spam", "spam", "spam", "spam",
        "ham", "ham", "ham", "ham", "ham",
    ]
    return texts, labels
