"""
Text Classification - A from-scratch implementation of text classification for learning NLP fundamentals.

This package implements:
- TF-IDF Vectorizer: Convert text to numerical features using Term Frequency-Inverse Document Frequency
- NaiveBayesClassifier: Probabilistic classifier based on Bayes' theorem with naive independence assumptions
- TextClassifier: High-level text classification pipeline combining TF-IDF and Naive Bayes
"""

from .tfidf import TFIDFVectorizer
from .naive_bayes import NaiveBayesClassifier
from .text_classifier import TextClassifier

__version__ = "0.1.0"
__all__ = ["TFIDFVectorizer", "NaiveBayesClassifier", "TextClassifier"]
