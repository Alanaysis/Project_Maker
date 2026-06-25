"""
Support Vector Machine (SVM) Classifier.

SVM is a supervised learning model that finds the optimal hyperplane to separate
classes with maximum margin.

Key concepts:
- Hyperplane: The decision boundary that separates classes
- Margin: The distance between the hyperplane and the nearest data points
- Support vectors: The data points closest to the hyperplane
- Kernel trick: Mapping data to higher dimensions for non-linear separation

For text classification, linear SVM often works well due to the high dimensionality
of text features.
"""

import math
from typing import Dict, List, Optional, Tuple


class SVMClassifier:
    """
    Support Vector Machine classifier using the Pegasos algorithm.

    This implementation uses the Pegasos (Primal Estimated sub-GrAdient
    SOlver for SVM) algorithm for efficient linear SVM training.

    Parameters
    ----------
    C : float, default=1.0
        Regularization parameter. Larger C means less regularization.
    max_iter : int, default=1000
        Maximum number of iterations.
    learning_rate : float, default=0.01
        Initial learning rate.
    """

    def __init__(
        self,
        C: float = 1.0,
        max_iter: int = 1000,
        learning_rate: float = 0.01,
    ):
        self.C = C
        self.max_iter = max_iter
        self.learning_rate = learning_rate

        # Learned attributes
        self.classes_: List[str] = []
        self.weights_: Dict[str, List[float]] = {}
        self.bias_: Dict[str, float] = {}
        self.n_features_: int = 0

    def _fit_binary(
        self,
        X: List[List[float]],
        y_binary: List[int],
    ) -> Tuple[List[float], float]:
        """
        Fit binary SVM using Pegasos algorithm.

        Parameters
        ----------
        X : list of list of float
            Feature matrix.
        y_binary : list of int
            Binary labels (-1 or 1).

        Returns
        -------
        tuple of (list of float, float)
            Learned weights and bias.
        """
        n_samples = len(X)
        n_features = len(X[0])

        # Initialize weights
        weights = [0.0] * n_features
        bias = 0.0

        # Pegasos algorithm
        for t in range(1, self.max_iter + 1):
            # Learning rate decreases over time
            eta = 1.0 / (self.learning_rate * t)

            # Random sample index
            i = (t - 1) % n_samples

            # Compute prediction
            score = bias
            for j in range(n_features):
                score += weights[j] * X[i][j]

            # Hinge loss condition
            if y_binary[i] * score < 1:
                # Update weights
                for j in range(n_features):
                    weights[j] = (1 - eta * self.learning_rate) * weights[j] + eta * self.C * y_binary[i] * X[i][j]
                bias += eta * self.C * y_binary[i]
            else:
                # Only regularization update
                for j in range(n_features):
                    weights[j] = (1 - eta * self.learning_rate) * weights[j]

        return weights, bias

    def fit(self, X: List[List[float]], y: List[str]) -> "SVMClassifier":
        """
        Fit SVM classifier according to X, y.

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
        self.classes_ = sorted(set(y))
        self.n_features_ = len(X[0]) if X else 0

        # Multi-class: One-vs-Rest (works for both binary and multi-class)
        for cls in self.classes_:
            binary_labels = [1 if label == cls else -1 for label in y]
            weights, bias = self._fit_binary(X, binary_labels)
            self.weights_[cls] = weights
            self.bias_[cls] = bias

        return self

    def decision_function(self, x: List[float]) -> Dict[str, float]:
        """
        Compute decision function values for a single sample.

        Parameters
        ----------
        x : list of float
            Feature vector.

        Returns
        -------
        dict
            Decision function value for each class.
        """
        scores = {}
        for cls in self.classes_:
            score = self.bias_[cls]
            for j in range(self.n_features_):
                score += self.weights_[cls][j] * x[j]
            scores[cls] = score
        return scores

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
            scores = self.decision_function(x)
            pred = max(scores.items(), key=lambda item: item[1])[0]
            predictions.append(pred)

        return predictions

    def predict_proba(self, X: List[List[float]]) -> List[Dict[str, float]]:
        """
        Return probability estimates using softmax of decision function.

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
            scores = self.decision_function(x)

            # Softmax
            max_score = max(scores.values())
            exp_scores = {cls: math.exp(score - max_score) for cls, score in scores.items()}
            total = sum(exp_scores.values())
            probs = {cls: exp / total for cls, exp in exp_scores.items()}

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
            "C": self.C,
            "max_iter": self.max_iter,
            "learning_rate": self.learning_rate,
        }
