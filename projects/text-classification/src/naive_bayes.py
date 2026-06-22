"""
Naive Bayes Classifier.

Naive Bayes is a family of probabilistic classifiers based on applying Bayes' theorem
with strong (naive) independence assumptions between the features.

Despite their naive design and apparently oversimplified assumptions, Naive Bayes
classifiers have worked quite well in many real-world situations, and are popular
for text classification.

Bayes' Theorem:
    P(y|X) = P(X|y) * P(y) / P(X)

Where:
    P(y|X) is the posterior probability of class y given features X
    P(X|y) is the likelihood of features X given class y
    P(y) is the prior probability of class y
    P(X) is the prior probability of features X

The "naive" assumption:
    P(X|y) = P(x1|y) * P(x2|y) * ... * P(xn|y)
    (features are conditionally independent given the class)

This implementation supports:
- Multinomial Naive Bayes: For discrete features (e.g., word counts, TF-IDF)
- Gaussian Naive Bayes: For continuous features (assumes Gaussian distribution)
"""

import math
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Union


class NaiveBayesClassifier:
    """
    Naive Bayes classifier for text classification.

    Supports both Multinomial and Gaussian variants.

    Parameters
    ----------
    alpha : float, default=1.0
        Additive (Laplace/Lidstone) smoothing parameter.
        0 for no smoothing, 1 for Laplace smoothing.
    model_type : str, default='multinomial'
        Type of Naive Bayes model. Options: 'multinomial', 'gaussian'.
    """

    def __init__(self, alpha: float = 1.0, model_type: str = "multinomial"):
        self.alpha = alpha
        self.model_type = model_type

        # Learned attributes
        self.class_log_prior_: Dict[str, float] = {}  # log P(y)
        self.feature_log_prob_: Dict[str, List[float]] = {}  # log P(x|y)
        self.classes_: List[str] = []  # unique classes
        self.n_features_: int = 0  # number of features

        # For Gaussian NB
        self.theta_: Dict[str, List[float]] = {}  # mean of each feature per class
        self.sigma_: Dict[str, List[float]] = {}  # variance of each feature per class

    def _compute_multinomial_probs(
        self, X: List[List[float]], y: List[str]
    ) -> None:
        """
        Compute feature probabilities for Multinomial Naive Bayes.

        Parameters
        ----------
        X : list of list of float
            Feature matrix (n_samples, n_features).
        y : list of str
            Target class labels.
        """
        n_samples = len(X)
        n_features = len(X[0]) if X else 0
        self.n_features_ = n_features

        # Count features per class
        feature_counts = defaultdict(lambda: [0.0] * n_features)
        class_counts = Counter()

        for i, (features, label) in enumerate(zip(X, y)):
            class_counts[label] += 1
            for j, value in enumerate(features):
                feature_counts[label][j] += value

        # Compute log probabilities
        for cls in self.classes_:
            # Prior probability: P(y)
            self.class_log_prior_[cls] = math.log(
                class_counts[cls] / n_samples
            )

            # Feature probabilities with smoothing: P(x|y)
            total_count = sum(feature_counts[cls]) + self.alpha * n_features
            self.feature_log_prob_[cls] = [
                math.log((feature_counts[cls][j] + self.alpha) / total_count)
                for j in range(n_features)
            ]

    def _compute_gaussian_probs(
        self, X: List[List[float]], y: List[str]
    ) -> None:
        """
        Compute feature statistics for Gaussian Naive Bayes.

        Parameters
        ----------
        X : list of list of float
            Feature matrix (n_samples, n_features).
        y : list of str
            Target class labels.
        """
        n_samples = len(X)
        n_features = len(X[0]) if X else 0
        self.n_features_ = n_features

        # Group samples by class
        class_samples = defaultdict(list)
        for features, label in zip(X, y):
            class_samples[label].append(features)

        # Compute mean and variance for each feature per class
        for cls in self.classes_:
            samples = class_samples[cls]
            n_class = len(samples)

            # Prior probability: P(y)
            self.class_log_prior_[cls] = math.log(n_class / n_samples)

            # Mean: theta = mean of each feature
            mean = [0.0] * n_features
            for j in range(n_features):
                mean[j] = sum(s[j] for s in samples) / n_class
            self.theta_[cls] = mean

            # Variance: sigma^2 = variance of each feature
            variance = [0.0] * n_features
            for j in range(n_features):
                variance[j] = (
                    sum((s[j] - mean[j]) ** 2 for s in samples) / n_class
                )
                # Add small epsilon to avoid zero variance
                variance[j] = max(variance[j], 1e-9)
            self.sigma_[cls] = variance

    def fit(self, X: List[List[float]], y: List[str]) -> "NaiveBayesClassifier":
        """
        Fit Naive Bayes classifier according to X, y.

        Parameters
        ----------
        X : list of list of float
            Training feature matrix (n_samples, n_features).
        y : list of str
            Target class labels (n_samples).

        Returns
        -------
        self
            Fitted classifier.
        """
        # Get unique classes
        self.classes_ = sorted(set(y))

        if self.model_type == "multinomial":
            self._compute_multinomial_probs(X, y)
        elif self.model_type == "gaussian":
            self._compute_gaussian_probs(X, y)
        else:
            raise ValueError(
                f"Unknown model_type: {self.model_type}. "
                f"Choose 'multinomial' or 'gaussian'."
            )

        return self

    def _predict_multinomial_single(self, x: List[float]) -> str:
        """
        Predict class for a single sample using Multinomial NB.

        Parameters
        ----------
        x : list of float
            Feature vector.

        Returns
        -------
        str
            Predicted class label.
        """
        best_class = None
        best_score = float("-inf")

        for cls in self.classes_:
            # Start with log prior
            score = self.class_log_prior_[cls]

            # Add log likelihood of features
            for j, value in enumerate(x):
                if value != 0:
                    score += value * self.feature_log_prob_[cls][j]

            if score > best_score:
                best_score = score
                best_class = cls

        return best_class

    def _predict_gaussian_single(self, x: List[float]) -> str:
        """
        Predict class for a single sample using Gaussian NB.

        Parameters
        ----------
        x : list of float
            Feature vector.

        Returns
        -------
        str
            Predicted class label.
        """
        best_class = None
        best_score = float("-inf")

        for cls in self.classes_:
            # Start with log prior
            score = self.class_log_prior_[cls]

            # Add log likelihood of features (Gaussian)
            for j, value in enumerate(x):
                mean = self.theta_[cls][j]
                variance = self.sigma_[cls][j]
                # Log of Gaussian PDF
                score -= 0.5 * math.log(2 * math.pi * variance)
                score -= 0.5 * ((value - mean) ** 2) / variance

            if score > best_score:
                best_score = score
                best_class = cls

        return best_class

    def predict(self, X: List[List[float]]) -> List[str]:
        """
        Perform classification on an array of test vectors X.

        Parameters
        ----------
        X : list of list of float
            Test feature matrix (n_samples, n_features).

        Returns
        -------
        list of str
            Predicted class labels for each sample.
        """
        if not self.classes_:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        predictions = []
        for x in X:
            if self.model_type == "multinomial":
                pred = self._predict_multinomial_single(x)
            else:
                pred = self._predict_gaussian_single(x)
            predictions.append(pred)

        return predictions

    def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
        """
        Return probability estimates for the test vector X.

        Parameters
        ----------
        X : list of list of float
            Test feature matrix (n_samples, n_features).

        Returns
        -------
        list of dict
            Probability of each class for each sample.
        """
        if not self.classes_:
            raise RuntimeError("Classifier has not been fitted. Call fit() first.")

        probabilities = []
        for x in X:
            # Compute log probabilities for each class
            log_probs = {}
            for cls in self.classes_:
                if self.model_type == "multinomial":
                    score = self.class_log_prior_[cls]
                    for j, value in enumerate(x):
                        if value != 0:
                            score += value * self.feature_log_prob_[cls][j]
                else:
                    score = self.class_log_prior_[cls]
                    for j, value in enumerate(x):
                        mean = self.theta_[cls][j]
                        variance = self.sigma_[cls][j]
                        score -= 0.5 * math.log(2 * math.pi * variance)
                        score -= 0.5 * ((value - mean) ** 2) / variance
                log_probs[cls] = score

            # Convert to probabilities using log-sum-exp trick
            max_log_prob = max(log_probs.values())
            exp_probs = {
                cls: math.exp(lp - max_log_prob)
                for cls, lp in log_probs.items()
            }
            total = sum(exp_probs.values())
            probs = {cls: ep / total for cls, ep in exp_probs.items()}

            probabilities.append(probs)

        return probabilities

    def score(self, X: List[List[float]], y: List[str]) -> float:
        """
        Return the mean accuracy on the given test data and labels.

        Parameters
        ----------
        X : list of list of float
            Test feature matrix.
        y : list of str
            True labels for X.

        Returns
        -------
        float
            Mean accuracy of self.predict(X) wrt. y.
        """
        predictions = self.predict(X)
        correct = sum(1 for pred, true in zip(predictions, y) if pred == true)
        return correct / len(y)

    def get_params(self) -> Dict:
        """
        Get parameters of the classifier.

        Returns
        -------
        dict
            Parameter names mapped to their values.
        """
        return {
            "alpha": self.alpha,
            "model_type": self.model_type,
        }
