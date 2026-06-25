"""
Tests for N-gram Vectorizer.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ngram import NGramVectorizer


class TestNGramVectorizer:
    """Test NGramVectorizer functionality."""

    def test_init(self):
        """Test vectorizer initialization."""
        vectorizer = NGramVectorizer()
        assert vectorizer.ngram_range == (1, 1)
        assert vectorizer.analyzer == "word"

    def test_init_with_params(self):
        """Test vectorizer initialization with custom parameters."""
        vectorizer = NGramVectorizer(
            ngram_range=(1, 2),
            max_features=100,
            analyzer="char",
        )
        assert vectorizer.ngram_range == (1, 2)
        assert vectorizer.max_features == 100
        assert vectorizer.analyzer == "char"

    def test_tokenize(self):
        """Test tokenization."""
        vectorizer = NGramVectorizer()
        tokens = vectorizer._tokenize("Hello, World!")
        assert tokens == ["hello", "world"]

    def test_generate_unigrams(self):
        """Test unigram generation."""
        vectorizer = NGramVectorizer(ngram_range=(1, 1))
        tokens = ["the", "cat", "sat"]
        ngrams = vectorizer._generate_ngrams(tokens)

        assert "the" in ngrams
        assert "cat" in ngrams
        assert "sat" in ngrams
        assert len(ngrams) == 3

    def test_generate_bigrams(self):
        """Test bigram generation."""
        vectorizer = NGramVectorizer(ngram_range=(2, 2))
        tokens = ["the", "cat", "sat"]
        ngrams = vectorizer._generate_ngrams(tokens)

        assert "the cat" in ngrams
        assert "cat sat" in ngrams
        assert len(ngrams) == 2

    def test_generate_unigrams_and_bigrams(self):
        """Test combined unigram and bigram generation."""
        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        tokens = ["the", "cat", "sat"]
        ngrams = vectorizer._generate_ngrams(tokens)

        assert "the" in ngrams
        assert "cat" in ngrams
        assert "sat" in ngrams
        assert "the cat" in ngrams
        assert "cat sat" in ngrams

    def test_generate_char_ngrams(self):
        """Test character n-gram generation."""
        vectorizer = NGramVectorizer(ngram_range=(2, 3), analyzer="char")
        ngrams = vectorizer._generate_char_ngrams("abc")

        assert "ab" in ngrams
        assert "bc" in ngrams
        assert "abc" in ngrams

    def test_fit_word_ngrams(self):
        """Test fitting with word n-grams."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]

        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        vectorizer.fit(documents)

        assert len(vectorizer.vocabulary_) > 0

    def test_transform_word_ngrams(self):
        """Test transforming with word n-grams."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]

        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        result = vectorizer.fit_transform(documents)

        assert len(result) == 2
        assert len(result[0]) == len(vectorizer.vocabulary_)

    def test_fit_transform(self):
        """Test fit_transform."""
        documents = ["the cat sat", "the dog ran"]
        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        result = vectorizer.fit_transform(documents)

        assert len(result) == 2

    def test_max_features(self):
        """Test max_features limit."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        vectorizer = NGramVectorizer(ngram_range=(1, 2), max_features=5)
        vectorizer.fit(documents)

        assert len(vectorizer.vocabulary_) <= 5

    def test_get_feature_names(self):
        """Test getting feature names."""
        documents = ["the cat sat"]
        vectorizer = NGramVectorizer(ngram_range=(1, 2))
        vectorizer.fit(documents)

        feature_names = vectorizer.get_feature_names()
        assert isinstance(feature_names, list)

    def test_get_params(self):
        """Test getting parameters."""
        vectorizer = NGramVectorizer(ngram_range=(1, 3), analyzer="char")
        params = vectorizer.get_params()

        assert params["ngram_range"] == (1, 3)
        assert params["analyzer"] == "char"

    def test_transform_before_fit(self):
        """Test that transform raises error before fit."""
        vectorizer = NGramVectorizer()
        with pytest.raises(RuntimeError):
            vectorizer.transform(["test"])

    def test_bigram_counts(self):
        """Test bigram counting."""
        documents = ["the cat sat on the cat mat"]
        vectorizer = NGramVectorizer(ngram_range=(2, 2))
        result = vectorizer.fit_transform(documents)

        # "the cat" appears twice
        if "the cat" in vectorizer.vocabulary_:
            idx = vectorizer.vocabulary_["the cat"]
            assert result[0][idx] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
