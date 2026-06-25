"""
Tests for Bag of Words Vectorizer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.bow import BagOfWordsVectorizer


class TestBagOfWordsVectorizer:
    """Test BagOfWordsVectorizer functionality."""

    def test_init(self):
        """Test vectorizer initialization."""
        vectorizer = BagOfWordsVectorizer()
        assert vectorizer.max_features is None
        assert vectorizer.min_df == 1
        assert vectorizer.max_df == 1.0
        assert vectorizer.binary is False

    def test_init_with_params(self):
        """Test vectorizer initialization with custom parameters."""
        vectorizer = BagOfWordsVectorizer(
            max_features=100,
            min_df=2,
            max_df=0.9,
            binary=True,
        )
        assert vectorizer.max_features == 100
        assert vectorizer.min_df == 2
        assert vectorizer.max_df == 0.9
        assert vectorizer.binary is True

    def test_tokenize(self):
        """Test tokenization."""
        vectorizer = BagOfWordsVectorizer()
        tokens = vectorizer._tokenize("Hello, World! This is a test.")
        assert tokens == ["hello", "world", "this", "is", "a", "test"]

    def test_fit(self):
        """Test fitting vectorizer."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        vectorizer = BagOfWordsVectorizer()
        vectorizer.fit(documents)

        assert len(vectorizer.vocabulary_) > 0
        assert len(vectorizer.feature_names_) > 0

    def test_transform(self):
        """Test transforming documents."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]

        vectorizer = BagOfWordsVectorizer()
        vectorizer.fit(documents)
        result = vectorizer.transform(documents)

        assert len(result) == 2
        assert len(result[0]) == len(vectorizer.vocabulary_)

    def test_fit_transform(self):
        """Test fit_transform."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]

        vectorizer = BagOfWordsVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 2

    def test_word_counts(self):
        """Test word counting."""
        documents = ["the cat sat on the mat"]
        vectorizer = BagOfWordsVectorizer()
        result = vectorizer.fit_transform(documents)

        # "the" appears twice
        the_idx = vectorizer.vocabulary_["the"]
        assert result[0][the_idx] == 2

        # "cat" appears once
        cat_idx = vectorizer.vocabulary_["cat"]
        assert result[0][cat_idx] == 1

    def test_binary_mode(self):
        """Test binary mode."""
        documents = ["the cat sat on the mat"]
        vectorizer = BagOfWordsVectorizer(binary=True)
        result = vectorizer.fit_transform(documents)

        # All counts should be 0 or 1
        for count in result[0]:
            assert count in [0, 1]

    def test_max_features(self):
        """Test max_features limit."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        vectorizer = BagOfWordsVectorizer(max_features=3)
        vectorizer.fit(documents)

        assert len(vectorizer.vocabulary_) <= 3

    def test_min_df(self):
        """Test minimum document frequency."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        # Word must appear in at least 2 documents
        vectorizer = BagOfWordsVectorizer(min_df=2)
        vectorizer.fit(documents)

        # "the" appears in 2 documents, should be included
        assert "the" in vectorizer.vocabulary_

        # "friends" appears in 1 document, should be excluded
        assert "friends" not in vectorizer.vocabulary_

    def test_get_feature_names(self):
        """Test getting feature names."""
        documents = ["the cat sat on the mat"]
        vectorizer = BagOfWordsVectorizer()
        vectorizer.fit(documents)

        feature_names = vectorizer.get_feature_names()
        assert isinstance(feature_names, list)
        assert len(feature_names) == len(vectorizer.vocabulary_)

    def test_get_params(self):
        """Test getting parameters."""
        vectorizer = BagOfWordsVectorizer(max_features=100, binary=True)
        params = vectorizer.get_params()

        assert params["max_features"] == 100
        assert params["binary"] is True

    def test_transform_before_fit(self):
        """Test that transform raises error before fit."""
        vectorizer = BagOfWordsVectorizer()
        with pytest.raises(RuntimeError):
            vectorizer.transform(["test"])

    def test_empty_document(self):
        """Test handling empty documents."""
        documents = ["", "the cat sat"]
        vectorizer = BagOfWordsVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 2
        # Empty document should have all zeros
        assert sum(result[0]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
