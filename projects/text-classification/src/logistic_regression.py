"""
Logistic Regression Classifier.

Logistic Regression is a linear model for classification that uses the logistic
(sigmoid) function to model the probability of a binary outcome.

For binary classification:
    P(y=1|x) = sigmoid(w^T * x + b) = 1 / (1 + exp(-(w^T * x + b)))

For multi-class classification (One-vs-Rest):
    Train one binary classifier per class, predict the class with highest probability.

The model is trained using gradient descent to minimize the log-loss:
    L = -1/n * sum(y * log(p) + (1-y) * log(1-p))
"""

import math
from typing import Dict, List, Optional, Tuple


class LogisticRegressionClassifier:
    """
    Logistic Regression classifier for text classification.

    Supports binary and multi-class classification using One-vs-Rest strategy.

    Parameters
    ----------
    learning_rate : float, default=0.01
        Learning rate for gradient descent.
    max_iter : int, default=1000
        Maximum number of iterations for gradient descent.
    regularization : float, default=0.01
        L2 regularization strength (lambda).
    tol : float, default=1e-4
        Tolerance for stopping criteria.
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        max_iter: int = 1000,
        regularization: float = 0.01,
        tol: float = 1e-4,
    ):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.regularization = regularization
        self.tol = tol

        # Learned attributes
        self.classes_: List[str] = []
        self.weights_: Dict[str, List[float]] = {}  # class -> weights
        self.bias_: Dict[str, float] = {}  # class -> bias
        self.n_features_: int = 0

    def _sigmoid(self, x: float) -> float:
        """
        Compute sigmoid function.

        Parameters
        ----------
        x : float
            Input value.

        Returns
        -------
        float
            Sigmoid output in range (0, 1).
        """
        # Clip to prevent overflow
        x = max(-500, min(500, x))
        return 1.0 / (1.0 + math.exp(-x))

    def _compute_gradient(
        self,
        X: List[List[float]],
        y_binary: List[int],
        weights: List[float],
        bias: float,
    ) -> Tuple[List[float], float]:
        """
        Compute gradients for logistic regression.

        Parameters
        ----------
        X : list of list of float
            Feature matrix.
        y_binary : list of int
            Binary labels (0 or 1).
        weights : list of float
            Current weights.
        bias : float
            Current bias.

        Returns
        -------
        tuple of (list of float, float)
            Weight gradients and bias gradient.
        """
        n_samples = len(X)
        n_features = len(X[0])

        dw = [0.0] * n_features
        db = 0.0

        for i in range(n_samples):
            # Compute prediction
            z = bias
            for j in range(n_features):
                z += weights[j] * X[i][j]
            pred = self._sigmoid(z)

            # Compute error
            error = pred - y_binary[i]

            # Accumulate gradients
            for j in range(n_features):
                dw[j] += error * X[i][j]
            db += error

        # Average gradients and add regularization
        for j in range(n_features):
            dw[j] = dw[j] / n_samples + self.regularization * weights[j]
        db = db / n_samples

        return dw, db

    def _fit_binary(
        self,
        X: List[List[float]],
        y_binary: List[int],
    ) -> Tuple[List[float], float]:
        """
        Fit binary logistic regression using gradient descent.

        Parameters
        ----------
        X : list of list of float
            Feature matrix.
        y_binary : list of int
            Binary labels (0 or 1).

        Returns
        -------
        tuple of (list of float, float)
            Learned weights and bias.
        """
        n_features = len(X[0])

        # Initialize weights
        weights = [0.0] * n_features
        bias = 0.0

        # Gradient descent
        for iteration in range(self.max_iter):
            dw, db = self._compute_gradient(X, y_binary, weights, bias)

            # Update weights
            for j in range(n_features):
                weights[j] -= self.learning_rate * dw[j]
            bias -= self.learning_rate * db

            # Check convergence
            gradient_norm = math.sqrt(sum(d * d for d in dw) + db * db)
            if gradient_norm < self.tol:
                break

        return weights, bias

    def fit(self, X: List[List[float]], y: List[str]) -> "LogisticRegressionClassifier":
        """
        Fit logistic regression classifier according to X, y.

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
            binary_labels = [1 if label == cls else 0 for label in y]
            weights, bias = self._fit_binary(X, binary_labels)
            self.weights_[cls] = weights
            self.bias_[cls] = bias

        return self

    def predict_proba_single(self, x: List[float]) -> Dict[str, float]:
        """
        Predict class probabilities for a single sample.

        Parameters
        ----------
        x : list of float
            Feature vector.

        Returns
        -------
        dict
            Probability of each class.
        """
        scores = {}
        for cls in self.classes_:
            z = self.bias_[cls]
            for j in range(self.n_features_):
                z += self.weights_[cls][j] * x[j]
            scores[cls] = self._sigmoid(z)

        # Normalize probabilities using softmax
        total = sum(scores.values())
        if total > 0:
            return {cls: score / total for cls, score in scores.items()}
        else:
            return {cls: 1.0 / len(self.classes_) for cls in self.classes_}

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
            proba = self.predict_proba_single(x)
            pred = max(proba.items(), key=lambda item: item[1])[0]
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

        return [self.predict_proba_single(x) for x in X]

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
            "learning_rate": self.learning_rate,
            "max_iter": self.max_iter,
            "regularization": self.regularization,
            "tol": self.tol,
        }
