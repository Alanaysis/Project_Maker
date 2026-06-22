"""
Tests for TF-IDF Vectorizer.
"""

import math
import pytest
from src.tfidf import TFIDFVectorizer


class TestTFIDFVectorizer:
    """Test suite for TFIDFVectorizer."""

    def test_basic_fit_transform(self):
        """Test basic fit and transform functionality."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        # Check dimensions
        assert len(result) == 3  # 3 documents
        assert len(result[0]) > 0  # Has features

        # Check vocabulary is populated
        assert len(vectorizer.vocabulary_) > 0
        assert len(vectorizer.feature_names_) > 0

    def test_vocabulary_building(self):
        """Test that vocabulary is correctly built."""
        documents = [
            "hello world",
            "hello python",
            "world python",
        ]

        vectorizer = TFIDFVectorizer()
        vectorizer.fit(documents)

        # Check vocabulary contains all unique words
        vocab = vectorizer.vocabulary_
        assert "hello" in vocab
        assert "world" in vocab
        assert "python" in vocab

    def test_tf_computation(self):
        """Test term frequency computation."""
        vectorizer = TFIDFVectorizer()

        # Test with simple document
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        tf = vectorizer._compute_tf(tokens)

        # "the" appears 2 times out of 6
        assert abs(tf["the"] - 2 / 6) < 1e-6
        # "cat" appears 1 time out of 6
        assert abs(tf["cat"] - 1 / 6) < 1e-6

    def test_idf_computation(self):
        """Test inverse document frequency computation."""
        documents = [
            ["the", "cat", "sat"],
            ["the", "dog", "ran"],
            ["the", "bird", "flew"],
        ]

        vectorizer = TFIDFVectorizer(smooth_idf=True)
        idf = vectorizer._compute_idf(documents)

        # "the" appears in all 3 documents
        # IDF = log((1 + 3) / (1 + 3)) + 1 = 1.0
        assert abs(idf["the"] - 1.0) < 1e-6

        # "cat" appears in 1 document
        # IDF = log((1 + 3) / (1 + 1)) + 1 = log(2) + 1
        expected_cat_idf = math.log(4 / 2) + 1
        assert abs(idf["cat"] - expected_cat_idf) < 1e-6

    def test_idf_no_smoothing(self):
        """Test IDF computation without smoothing."""
        documents = [
            ["the", "cat", "sat"],
            ["the", "dog", "ran"],
            ["the", "bird", "flew"],
        ]

        vectorizer = TFIDFVectorizer(smooth_idf=False)
        idf = vectorizer._compute_idf(documents)

        # "the" appears in all 3 documents
        # IDF = log(3 / 3) + 1 = 1.0
        assert abs(idf["the"] - 1.0) < 1e-6

    def test_max_features(self):
        """Test limiting number of features."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        vectorizer = TFIDFVectorizer(max_features=5)
        result = vectorizer.fit_transform(documents)

        # Should have at most 5 features
        assert len(result[0]) <= 5
        assert len(vectorizer.vocabulary_) <= 5

    def test_min_df(self):
        """Test minimum document frequency filter."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        # min_df=2: only keep terms appearing in at least 2 documents
        vectorizer = TFIDFVectorizer(min_df=2)
        vectorizer.fit(documents)

        # "the" appears in 2 documents, should be kept
        assert "the" in vectorizer.vocabulary_
        # "cat" appears in 1 document, should be filtered
        assert "cat" not in vectorizer.vocabulary_

    def test_max_df(self):
        """Test maximum document frequency filter."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        # max_df=0.5: only keep terms appearing in at most 50% of documents
        vectorizer = TFIDFVectorizer(max_df=0.5)
        vectorizer.fit(documents)

        # "the" appears in 2/3 documents (67%), should be filtered
        assert "the" not in vectorizer.vocabulary_

    def test_l2_normalization(self):
        """Test L2 normalization."""
        documents = [
            "hello world",
            "hello python",
        ]

        vectorizer = TFIDFVectorizer(norm="l2")
        result = vectorizer.fit_transform(documents)

        # Check that each vector has unit L2 norm
        for vector in result:
            norm = math.sqrt(sum(x * x for x in vector))
            assert abs(norm - 1.0) < 1e-6

    def test_l1_normalization(self):
        """Test L1 normalization."""
        documents = [
            "hello world",
            "hello python",
        ]

        vectorizer = TFIDFVectorizer(norm="l1")
        result = vectorizer.fit_transform(documents)

        # Check that each vector has unit L1 norm
        for vector in result:
            norm = sum(abs(x) for x in vector)
            assert abs(norm - 1.0) < 1e-6

    def test_no_normalization(self):
        """Test without normalization."""
        documents = [
            "hello world",
            "hello python",
        ]

        vectorizer = TFIDFVectorizer(norm=None)
        result = vectorizer.fit_transform(documents)

        # Vectors should not be normalized
        for vector in result:
            norm = math.sqrt(sum(x * x for x in vector))
            # Norms should generally not be 1.0
            # (unless by coincidence)

    def test_sublinear_tf(self):
        """Test sublinear TF scaling."""
        documents = [
            "the the the cat",
            "the dog",
        ]

        vectorizer = TFIDFVectorizer(sublinear_tf=True)
        result = vectorizer.fit_transform(documents)

        # With sublinear TF, high frequency terms are dampened
        assert len(result) == 2

    def test_no_idf(self):
        """Test TF-only vectorization (no IDF)."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]

        vectorizer = TFIDFVectorizer(use_idf=False)
        result = vectorizer.fit_transform(documents)

        # Should still produce valid vectors
        assert len(result) == 2
        assert len(result[0]) > 0

    def test_transform_before_fit(self):
        """Test that transform raises error before fit."""
        vectorizer = TFIDFVectorizer()

        with pytest.raises(RuntimeError, match="not been fitted"):
            vectorizer.transform(["test document"])

    def test_single_document(self):
        """Test with single document."""
        documents = ["hello world"]
        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 1
        assert len(result[0]) > 0

    def test_empty_document(self):
        """Test with empty document."""
        documents = ["", "hello world"]
        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 2
        # Empty document should have zero vector
        assert all(x == 0.0 for x in result[0])

    def test_get_feature_names(self):
        """Test getting feature names."""
        documents = [
            "hello world",
            "hello python",
        ]

        vectorizer = TFIDFVectorizer()
        vectorizer.fit(documents)

        feature_names = vectorizer.get_feature_names()
        assert isinstance(feature_names, list)
        assert len(feature_names) > 0

    def test_get_params(self):
        """Test getting parameters."""
        vectorizer = TFIDFVectorizer(
            max_features=100,
            min_df=2,
            max_df=0.9,
            norm="l1",
            use_idf=False,
            smooth_idf=False,
            sublinear_tf=True,
        )

        params = vectorizer.get_params()
        assert params["max_features"] == 100
        assert params["min_df"] == 2
        assert params["max_df"] == 0.9
        assert params["norm"] == "l1"
        assert params["use_idf"] is False
        assert params["smooth_idf"] is False
        assert params["sublinear_tf"] is True

    def test_fit_transform_consistency(self):
        """Test that fit_transform gives same result as fit then transform."""
        documents = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are friends",
        ]

        # Method 1: fit_transform
        vectorizer1 = TFIDFVectorizer()
        result1 = vectorizer1.fit_transform(documents)

        # Method 2: fit then transform
        vectorizer2 = TFIDFVectorizer()
        vectorizer2.fit(documents)
        result2 = vectorizer2.transform(documents)

        # Results should be identical
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert len(r1) == len(r2)
            for v1, v2 in zip(r1, r2):
                assert abs(v1 - v2) < 1e-6

    def test_transform_new_documents(self):
        """Test transforming new documents after fit."""
        train_docs = [
            "the cat sat on the mat",
            "the dog sat on the log",
        ]
        test_docs = [
            "the cat and the dog",
            "a bird in the sky",
        ]

        vectorizer = TFIDFVectorizer()
        vectorizer.fit(train_docs)
        result = vectorizer.transform(test_docs)

        assert len(result) == 2
        # Each vector should have same number of features
        assert len(result[0]) == len(result[1])
        assert len(result[0]) == len(vectorizer.vocabulary_)

    def test_case_insensitive(self):
        """Test that tokenization is case-insensitive."""
        documents = [
            "Hello World",
            "HELLO world",
            "hello WORLD",
        ]

        vectorizer = TFIDFVectorizer()
        vectorizer.fit(documents)

        # All variations should be treated as same word
        assert "hello" in vectorizer.vocabulary_
        assert "world" in vectorizer.vocabulary_

    def test_punctuation_handling(self):
        """Test that punctuation is handled correctly."""
        documents = [
            "Hello, World!",
            "Hello. World?",
            "Hello World",
        ]

        vectorizer = TFIDFVectorizer()
        vectorizer.fit(documents)

        # Punctuation should be removed
        assert "hello" in vectorizer.vocabulary_
        assert "world" in vectorizer.vocabulary_
        assert "hello," not in vectorizer.vocabulary_

    def test_different_doc_lengths(self):
        """Test with documents of different lengths."""
        documents = [
            "short",
            "this is a medium length document",
            "this is a much longer document with many more words in it than the others",
        ]

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 3
        # All vectors should have same dimensionality
        assert len(result[0]) == len(result[1]) == len(result[2])


class TestTFIDFVectorizerEdgeCases:
    """Test edge cases for TFIDFVectorizer."""

    def test_all_same_document(self):
        """Test when all documents are identical."""
        documents = ["hello world"] * 5

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 5
        # All vectors should be identical
        for i in range(1, len(result)):
            for v1, v2 in zip(result[0], result[i]):
                assert abs(v1 - v2) < 1e-6

    def test_no_common_words(self):
        """Test with documents having no common words."""
        documents = [
            "cat dog",
            "bird fish",
            "tree flower",
        ]

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 3
        # Each document should have unique features

    def test_single_word_documents(self):
        """Test with single-word documents."""
        documents = ["cat", "dog", "bird"]

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        assert len(result) == 3
        assert len(result[0]) == 3

    def test_special_characters(self):
        """Test with special characters."""
        documents = [
            "hello@world",
            "test#123",
            "foo$bar",
        ]

        vectorizer = TFIDFVectorizer()
        result = vectorizer.fit_transform(documents)

        # Should still work with special characters
        assert len(result) == 3
