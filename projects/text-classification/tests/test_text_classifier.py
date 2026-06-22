"""
Tests for Text Classifier.
"""

import pytest
from src.text_classifier import TextClassifier


class TestTextClassifier:
    """Test suite for TextClassifier."""

    def test_basic_fit_predict(self):
        """Test basic fit and predict functionality."""
        texts = [
            "I love this movie, it is great",
            "This movie is excellent and wonderful",
            "I hate this movie, it is terrible",
            "This movie is awful and boring",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        # Should be fitted
        assert classifier.is_fitted is True

    def test_predict(self):
        """Test prediction on new texts."""
        texts = [
            "I love this movie, it is great",
            "This movie is excellent and wonderful",
            "I hate this movie, it is terrible",
            "This movie is awful and boring",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        # Test predictions
        test_texts = [
            "This movie is great and wonderful",
            "This movie is terrible and awful",
        ]
        predictions = classifier.predict(test_texts)

        assert len(predictions) == 2
        assert predictions[0] == "positive"
        assert predictions[1] == "negative"

    def test_predict_proba(self):
        """Test probability predictions."""
        texts = [
            "I love this movie",
            "This movie is great",
            "I hate this movie",
            "This movie is terrible",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        probas = classifier.predict_proba(["This movie is great"])

        assert len(probas) == 1
        assert "positive" in probas[0]
        assert "negative" in probas[0]

        # Probabilities should sum to 1
        total = sum(probas[0].values())
        assert abs(total - 1.0) < 1e-6

        # Positive should have higher probability
        assert probas[0]["positive"] > probas[0]["negative"]

    def test_score(self):
        """Test accuracy scoring."""
        texts = [
            "I love this movie",
            "This movie is great",
            "I hate this movie",
            "This movie is terrible",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        score = classifier.score(texts, labels)
        assert score == 1.0

    def test_predict_before_fit(self):
        """Test that predict raises error before fit."""
        classifier = TextClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            classifier.predict(["test text"])

    def test_predict_proba_before_fit(self):
        """Test that predict_proba raises error before fit."""
        classifier = TextClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            classifier.predict_proba(["test text"])

    def test_score_before_fit(self):
        """Test that score raises error before fit."""
        classifier = TextClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            classifier.score(["test text"], ["label"])

    def test_different_lengths_raises_error(self):
        """Test that mismatched lengths raise error."""
        texts = ["text1", "text2"]
        labels = ["label1"]

        classifier = TextClassifier()

        with pytest.raises(ValueError, match="same length"):
            classifier.fit(texts, labels)

    def test_get_top_features(self):
        """Test getting top features per class."""
        texts = [
            "the cat sat on the mat",
            "the dog played in the park",
            "cats are cute pets",
            "dogs are loyal animals",
        ]
        labels = ["cat", "dog", "cat", "dog"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        top_features = classifier.get_top_features(n=5)

        assert "cat" in top_features
        assert "dog" in top_features

        # Each class should have feature lists
        for cls, features in top_features.items():
            assert isinstance(features, list)
            assert len(features) <= 5
            for feature, importance in features:
                assert isinstance(feature, str)
                assert isinstance(importance, float)

    def test_get_top_features_before_fit(self):
        """Test that get_top_features raises error before fit."""
        classifier = TextClassifier()

        with pytest.raises(RuntimeError, match="not been fitted"):
            classifier.get_top_features()

    def test_get_params(self):
        """Test getting parameters."""
        classifier = TextClassifier(
            max_features=100,
            alpha=0.5,
            norm="l1",
            use_idf=False,
            sublinear_tf=True,
        )

        params = classifier.get_params()
        assert params["max_features"] == 100
        assert params["alpha"] == 0.5
        assert params["norm"] == "l1"
        assert params["use_idf"] is False
        assert params["sublinear_tf"] is True

    def test_multiple_classes(self):
        """Test with multiple classes."""
        texts = [
            "I love programming in Python",
            "Python is a great language",
            "I enjoy cooking Italian food",
            "Italian cuisine is delicious",
            "The weather is sunny today",
            "Today is a beautiful day",
        ]
        labels = ["tech", "tech", "food", "food", "weather", "weather"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        test_texts = [
            "Python programming is fun",
            "I like pasta and pizza",
            "It is raining outside",
        ]
        predictions = classifier.predict(test_texts)

        assert len(predictions) == 3
        assert predictions[0] == "tech"
        assert predictions[1] == "food"
        assert predictions[2] == "weather"

    def test_single_class(self):
        """Test with single class."""
        texts = [
            "hello world",
            "goodbye world",
        ]
        labels = ["single", "single"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        predictions = classifier.predict(["hello"])
        assert predictions[0] == "single"

    def test_long_texts(self):
        """Test with longer texts."""
        texts = [
            "This is a very long positive review about a movie. " * 10,
            "Another long positive review with great words. " * 10,
            "This is a very long negative review about a movie. " * 10,
            "Another long negative review with terrible words. " * 10,
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        predictions = classifier.predict(["This is a great movie with wonderful acting."])
        assert predictions[0] == "positive"

    def test_short_texts(self):
        """Test with short texts."""
        texts = [
            "good",
            "great",
            "bad",
            "terrible",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        predictions = classifier.predict(["good"])
        assert predictions[0] == "positive"

    def test_mixed_case(self):
        """Test that case is handled correctly."""
        texts = [
            "I LOVE this movie",
            "This Movie is GREAT",
            "I HATE this movie",
            "This Movie is TERRIBLE",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        predictions = classifier.predict(["this movie is great"])
        assert predictions[0] == "positive"

    def test_punctuation_handling(self):
        """Test that punctuation is handled correctly."""
        texts = [
            "I love this movie!",
            "This movie is great.",
            "I hate this movie?",
            "This movie is terrible...",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        predictions = classifier.predict(["This movie is great!"])
        assert predictions[0] == "positive"

    def test_custom_parameters(self):
        """Test with custom parameters."""
        texts = [
            "I love this movie",
            "This movie is great",
            "I hate this movie",
            "This movie is terrible",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier(
            max_features=10,
            alpha=0.5,
            norm="l1",
            use_idf=True,
            sublinear_tf=True,
        )
        classifier.fit(texts, labels)

        predictions = classifier.predict(["This movie is great"])
        assert predictions[0] == "positive"


class TestTextClassifierIntegration:
    """Integration tests for TextClassifier."""

    def test_sentiment_analysis(self):
        """Test sentiment analysis scenario."""
        # Training data
        texts = [
            "This movie is absolutely wonderful and amazing",
            "I really enjoyed this film, it was fantastic",
            "The acting was superb and the story was compelling",
            "This is the worst movie I have ever seen",
            "Terrible acting and a boring storyline",
            "I wasted two hours of my life watching this garbage",
        ]
        labels = [
            "positive", "positive", "positive",
            "negative", "negative", "negative",
        ]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        # Test
        test_texts = [
            "This film was amazing and I loved it",
            "What a terrible waste of time",
        ]
        predictions = classifier.predict(test_texts)

        assert predictions[0] == "positive"
        assert predictions[1] == "negative"

    def test_topic_classification(self):
        """Test topic classification scenario."""
        texts = [
            "The stock market crashed today losing 500 points",
            "Investors are worried about the economic downturn",
            "Apple released a new iPhone with amazing features",
            "The latest Android update includes many improvements",
            "The football team won the championship game",
            "The basketball player scored 50 points in the game",
        ]
        labels = [
            "finance", "finance",
            "technology", "technology",
            "sports", "sports",
        ]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        test_texts = [
            "The Dow Jones index fell sharply today",
            "Google announced a new AI assistant",
            "The team scored a touchdown in the final seconds",
        ]
        predictions = classifier.predict(test_texts)

        assert predictions[0] == "finance"
        assert predictions[1] == "technology"
        assert predictions[2] == "sports"

    def test_spam_detection(self):
        """Test spam detection scenario."""
        texts = [
            "You have won a million dollars! Click here now!",
            "Congratulations! You are our lucky winner!",
            "Free money! No strings attached!",
            "Hey, are you coming to the party tonight?",
            "The meeting is scheduled for tomorrow at 3pm",
            "Can you send me the report by end of day?",
        ]
        labels = [
            "spam", "spam", "spam",
            "ham", "ham", "ham",
        ]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        test_texts = [
            "You have been selected to win a prize!",
            "Don't forget about our meeting tomorrow",
        ]
        predictions = classifier.predict(test_texts)

        assert predictions[0] == "spam"
        assert predictions[1] == "ham"

    def test_confidence_scores(self):
        """Test that confidence scores are meaningful."""
        texts = [
            "I love this movie",
            "This movie is great",
            "I hate this movie",
            "This movie is terrible",
        ]
        labels = ["positive", "positive", "negative", "negative"]

        classifier = TextClassifier()
        classifier.fit(texts, labels)

        # High confidence prediction using words from training data
        probas = classifier.predict_proba(["I love great movie"])
        # Should have higher probability for positive
        assert probas[0]["positive"] > probas[0]["negative"]

        # Negative prediction using words from training data
        probas = classifier.predict_proba(["I hate terrible movie"])
        # Should have higher probability for negative
        assert probas[0]["negative"] > probas[0]["positive"]
