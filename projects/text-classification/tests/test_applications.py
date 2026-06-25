"""
Tests for Applications (Sentiment Analysis, News Classification, Spam Detection).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.applications import (
    SentimentAnalyzer,
    NewsClassifier,
    SpamDetector,
    create_sample_sentiment_data,
    create_sample_news_data,
    create_sample_spam_data,
)


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer functionality."""

    def test_init(self):
        """Test initialization."""
        analyzer = SentimentAnalyzer(classifier_type="naive_bayes")
        assert analyzer.classifier_type == "naive_bayes"

    def test_init_invalid_classifier(self):
        """Test initialization with invalid classifier."""
        with pytest.raises(ValueError):
            SentimentAnalyzer(classifier_type="invalid")

    def test_fit_predict(self):
        """Test fit and predict."""
        texts, labels = create_sample_sentiment_data()

        analyzer = SentimentAnalyzer(classifier_type="naive_bayes")
        analyzer.fit(texts, labels)

        predictions = analyzer.predict(["I love this!", "This is terrible."])
        assert len(predictions) == 2
        assert predictions[0] in ["positive", "negative"]
        assert predictions[1] in ["positive", "negative"]

    def test_predict_proba(self):
        """Test probability prediction."""
        texts, labels = create_sample_sentiment_data()

        analyzer = SentimentAnalyzer(classifier_type="naive_bayes")
        analyzer.fit(texts, labels)

        probas = analyzer.predict_proba(["I love this!"])
        assert len(probas) == 1
        assert "positive" in probas[0]
        assert "negative" in probas[0]

    def test_evaluate(self):
        """Test evaluation."""
        texts, labels = create_sample_sentiment_data()

        analyzer = SentimentAnalyzer(classifier_type="naive_bayes")
        analyzer.fit(texts, labels)

        metrics = analyzer.evaluate(texts, labels)
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics

    def test_logistic_regression(self):
        """Test with logistic regression."""
        texts, labels = create_sample_sentiment_data()

        analyzer = SentimentAnalyzer(classifier_type="logistic_regression")
        analyzer.fit(texts, labels)

        predictions = analyzer.predict(["Great movie!"])
        assert len(predictions) == 1

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        analyzer = SentimentAnalyzer()
        with pytest.raises(RuntimeError):
            analyzer.predict(["test"])


class TestNewsClassifier:
    """Test NewsClassifier functionality."""

    def test_init(self):
        """Test initialization."""
        classifier = NewsClassifier(classifier_type="logistic_regression")
        assert classifier.classifier_type == "logistic_regression"

    def test_fit_predict(self):
        """Test fit and predict."""
        texts, labels = create_sample_news_data()

        classifier = NewsClassifier(classifier_type="naive_bayes")
        classifier.fit(texts, labels)

        predictions = classifier.predict(["The team won the game."])
        assert len(predictions) == 1
        assert predictions[0] in ["sports", "politics", "technology", "finance"]

    def test_predict_proba(self):
        """Test probability prediction."""
        texts, labels = create_sample_news_data()

        classifier = NewsClassifier(classifier_type="naive_bayes")
        classifier.fit(texts, labels)

        probas = classifier.predict_proba(["The team won the game."])
        assert len(probas) == 1
        assert abs(sum(probas[0].values()) - 1.0) < 1e-6

    def test_evaluate(self):
        """Test evaluation."""
        texts, labels = create_sample_news_data()

        classifier = NewsClassifier(classifier_type="naive_bayes")
        classifier.fit(texts, labels)

        metrics = classifier.evaluate(texts, labels)
        assert "accuracy" in metrics
        assert "precision_macro" in metrics
        assert "recall_macro" in metrics
        assert "f1_macro" in metrics


class TestSpamDetector:
    """Test SpamDetector functionality."""

    def test_init(self):
        """Test initialization."""
        detector = SpamDetector(classifier_type="naive_bayes")
        assert detector.classifier_type == "naive_bayes"

    def test_fit_predict(self):
        """Test fit and predict."""
        texts, labels = create_sample_spam_data()

        detector = SpamDetector(classifier_type="naive_bayes")
        detector.fit(texts, labels)

        predictions = detector.predict(["Congratulations! You won a prize!"])
        assert len(predictions) == 1
        assert predictions[0] in ["spam", "ham"]

    def test_predict_proba(self):
        """Test probability prediction."""
        texts, labels = create_sample_spam_data()

        detector = SpamDetector(classifier_type="naive_bayes")
        detector.fit(texts, labels)

        probas = detector.predict_proba(["Free money! Click now!"])
        assert len(probas) == 1
        assert "spam" in probas[0]
        assert "ham" in probas[0]

    def test_evaluate(self):
        """Test evaluation."""
        texts, labels = create_sample_spam_data()

        detector = SpamDetector(classifier_type="naive_bayes")
        detector.fit(texts, labels)

        metrics = detector.evaluate(texts, labels)
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1" in metrics


class TestSampleData:
    """Test sample data creation functions."""

    def test_sentiment_data(self):
        """Test sentiment data creation."""
        texts, labels = create_sample_sentiment_data()

        assert len(texts) == len(labels)
        assert len(texts) > 0
        assert all(label in ["positive", "negative"] for label in labels)

    def test_news_data(self):
        """Test news data creation."""
        texts, labels = create_sample_news_data()

        assert len(texts) == len(labels)
        assert len(texts) > 0
        assert all(label in ["sports", "politics", "technology", "finance"] for label in labels)

    def test_spam_data(self):
        """Test spam data creation."""
        texts, labels = create_sample_spam_data()

        assert len(texts) == len(labels)
        assert len(texts) > 0
        assert all(label in ["spam", "ham"] for label in labels)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
