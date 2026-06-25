"""
Text Classification - A from-scratch implementation of text classification for learning NLP fundamentals.

This package implements:
- Feature Extraction:
  - BagOfWordsVectorizer: Convert text to word count vectors
  - TFIDFVectorizer: Convert text to TF-IDF feature vectors
  - NGramVectorizer: Extract N-gram features

- Traditional Classifiers:
  - NaiveBayesClassifier: Probabilistic classifier based on Bayes' theorem
  - LogisticRegressionClassifier: Linear classifier using logistic function
  - SVMClassifier: Support Vector Machine using Pegasos algorithm

- Deep Learning Models (NumPy only):
  - TextCNN: Convolutional Neural Network for text
  - LSTMModel: Long Short-Term Memory network
  - BiLSTMAttention: Bidirectional LSTM with Attention mechanism

- Evaluation:
  - accuracy, precision, recall, f1_score
  - confusion_matrix, classification_report

- Applications:
  - SentimentAnalyzer: Sentiment analysis
  - NewsClassifier: News categorization
  - SpamDetector: Spam detection
"""

# Feature extraction
from .bow import BagOfWordsVectorizer
from .tfidf import TFIDFVectorizer
from .ngram import NGramVectorizer

# Traditional classifiers
from .naive_bayes import NaiveBayesClassifier
from .logistic_regression import LogisticRegressionClassifier
from .svm_classifier import SVMClassifier

# Deep learning models
from .deep_learning import TextCNN, LSTMModel, BiLSTMAttention

# Evaluation
from .evaluation import (
    accuracy,
    precision,
    recall,
    f1_score,
    confusion_matrix,
    classification_report,
    evaluate_classifier,
)

# Applications
from .applications import (
    SentimentAnalyzer,
    NewsClassifier,
    SpamDetector,
    create_sample_sentiment_data,
    create_sample_news_data,
    create_sample_spam_data,
)

# Pipeline
from .text_classifier import TextClassifier

__version__ = "0.2.0"

__all__ = [
    # Feature extraction
    "BagOfWordsVectorizer",
    "TFIDFVectorizer",
    "NGramVectorizer",
    # Traditional classifiers
    "NaiveBayesClassifier",
    "LogisticRegressionClassifier",
    "SVMClassifier",
    # Deep learning
    "TextCNN",
    "LSTMModel",
    "BiLSTMAttention",
    # Evaluation
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "confusion_matrix",
    "classification_report",
    "evaluate_classifier",
    # Applications
    "SentimentAnalyzer",
    "NewsClassifier",
    "SpamDetector",
    "create_sample_sentiment_data",
    "create_sample_news_data",
    "create_sample_spam_data",
    # Pipeline
    "TextClassifier",
]
