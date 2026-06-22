"""
Random Forest Classifier - An ensemble of decision trees using bagging and random feature selection.

This module implements a Random Forest classifier that:
1. Creates multiple bootstrap samples (bagging) from the training data
2. Trains a decision tree on each bootstrap sample
3. At each split, randomly selects a subset of features (random feature selection)
4. Combines predictions via majority voting (ensemble voting)

The key insight is that combining many "weak" learners (trees with limited
features) can create a "strong" learner with better generalization.
"""

import numpy as np
from typing import Optional, List, Any, Tuple
from .decision_tree import DecisionTreeClassifier


class RandomForestClassifier:
    """A Random Forest classifier.

    This implements the core Random Forest algorithm:

    For each tree (n_estimators times):
        1. Bootstrap: Draw a random sample with replacement from the training data
        2. Train: Build a decision tree on the bootstrap sample
           - At each node, randomly select max_features features to consider
           - Find the best split among only those features
        3. Store the trained tree

    For prediction:
        - Each tree predicts independently
        - Final prediction is the majority vote of all trees

    Parameters:
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree. None means unlimited.
        min_samples_split: Minimum samples to split a node.
        min_samples_leaf: Minimum samples at a leaf node.
        max_features: Number of features to consider at each split.
            - If "sqrt" (default): sqrt(n_features)
            - If "log2": log2(n_features)
            - If int: that exact number
            - If float: fraction of total features
            - If None: all features (no feature randomness)
        bootstrap: Whether to use bootstrap sampling. If False, the entire
            dataset is used for each tree (still with random feature selection).
        criterion: Split quality measure ('gini' or 'entropy').
        random_state: Random seed for reproducibility.
        n_jobs: Not used (included for API compatibility). Trees are built sequentially.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Any = "sqrt",
        bootstrap: bool = True,
        criterion: str = "gini",
        random_state: Optional[int] = None,
        n_jobs: Optional[int] = None,
    ):
        if n_estimators < 1:
            raise ValueError("n_estimators must be at least 1")

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.criterion = criterion
        self.random_state = random_state
        self.n_jobs = n_jobs

        self.trees_: List[DecisionTreeClassifier] = []
        self.classes_: np.ndarray = np.array([])
        self.n_classes_: int = 0
        self.n_features_: int = 0
        self.feature_importances_: Optional[np.ndarray] = None
        self.oob_score_: Optional[float] = None

        self._rng = np.random.RandomState(random_state)

    def _bootstrap_sample(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create a bootstrap sample of the training data.

        Bootstrap sampling draws n_samples random indices WITH replacement,
        so some samples will appear multiple times and some will be left out.
        The left-out samples (~37% on average) form the "out-of-bag" (OOB) set.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target labels (n_samples,).

        Returns:
            Tuple of (X_bootstrap, y_bootstrap, oob_indices).
        """
        n_samples = len(X)
        indices = self._rng.choice(n_samples, size=n_samples, replace=True)

        # Find out-of-bag indices (samples not selected)
        all_indices = set(range(n_samples))
        selected_indices = set(indices)
        oob_indices = np.array(sorted(all_indices - selected_indices))

        return X[indices], y[indices], oob_indices

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestClassifier":
        """Build the random forest from training data.

        This is the main training loop:

        For each tree:
            1. If bootstrap=True, create a bootstrap sample
            2. Create a DecisionTreeClassifier with feature subsampling
            3. Train the tree on the bootstrap sample
            4. Store the tree

        After all trees are trained, compute:
            - Feature importances (averaged across all trees)
            - Out-of-bag score (if bootstrap=True)

        Args:
            X: Training feature matrix (n_samples, n_features).
            y: Target labels (n_samples,).

        Returns:
            self: The fitted classifier.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if len(X) != len(y):
            raise ValueError("X and y must have the same number of samples")

        self.n_features_ = X.shape[1]
        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)

        if self.n_classes_ < 2:
            raise ValueError("Need at least 2 classes for classification")

        self.trees_ = []

        # Track OOB predictions for OOB score calculation
        if self.bootstrap:
            oob_predictions = np.zeros((len(X), self.n_classes_))
            oob_counts = np.zeros(len(X))

        for i in range(self.n_estimators):
            # Use a different random seed for each tree but reproducible
            tree_seed = self._rng.randint(0, 2**31)

            # Create bootstrap sample or use full dataset
            if self.bootstrap:
                X_sample, y_sample, oob_indices = self._bootstrap_sample(X, y)
            else:
                X_sample, y_sample = X, y
                oob_indices = np.array([])

            # Create and train a decision tree with feature subsampling
            tree = DecisionTreeClassifier(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                criterion=self.criterion,
                max_features=self.max_features,
                random_state=tree_seed,
            )
            tree.fit(X_sample, y_sample)
            self.trees_.append(tree)

            # Accumulate OOB predictions
            if self.bootstrap and len(oob_indices) > 0:
                oob_preds = tree.predict(X[oob_indices])
                for idx, pred in zip(oob_indices, oob_preds):
                    class_idx = np.searchsorted(self.classes_, pred)
                    oob_predictions[idx, class_idx] += 1
                    oob_counts[idx] += 1

        # Compute feature importances (average across all trees)
        self.feature_importances_ = np.zeros(self.n_features_)
        for tree in self.trees_:
            if tree.feature_importances_ is not None:
                self.feature_importances_ += tree.feature_importances_
        self.feature_importances_ /= self.n_estimators

        # Compute OOB score
        if self.bootstrap:
            oob_mask = oob_counts > 0
            if np.any(oob_mask):
                oob_pred_classes = self.classes_[
                    np.argmax(oob_predictions[oob_mask], axis=1)
                ]
                self.oob_score_ = np.mean(oob_pred_classes == y[oob_mask])
            else:
                self.oob_score_ = None

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels using majority voting.

        Each tree in the forest predicts independently. The final prediction
        is the class that receives the most votes (majority voting).

        This is the core ensemble mechanism:
            - Each tree has seen a different bootstrap sample
            - Each tree has considered different features at each split
            - Combining their predictions reduces variance and overfitting

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of predicted class labels.
        """
        if not self.trees_:
            raise RuntimeError("Forest has not been fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]

        # Collect predictions from all trees
        # Shape: (n_estimators, n_samples)
        all_predictions = np.array([tree.predict(X) for tree in self.trees_])

        # Majority voting for each sample
        predictions = np.empty(n_samples, dtype=self.classes_.dtype)
        for i in range(n_samples):
            # Get votes for this sample from all trees
            votes = all_predictions[:, i]
            # Count votes for each class
            vote_counts = Counter(votes)
            # Class with most votes wins
            predictions[i] = vote_counts.most_common(1)[0][0]

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Instead of just the majority vote, returns the fraction of trees
        that voted for each class. This gives a measure of confidence.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of shape (n_samples, n_classes) with class probabilities.
        """
        if not self.trees_:
            raise RuntimeError("Forest has not been fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]

        # Collect predictions from all trees
        all_predictions = np.array([tree.predict(X) for tree in self.trees_])

        # Calculate probabilities as fraction of votes
        proba = np.zeros((n_samples, self.n_classes_))
        for i in range(n_samples):
            votes = all_predictions[:, i]
            for j, cls in enumerate(self.classes_):
                proba[i, j] = np.sum(votes == cls) / self.n_estimators

        return proba

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Calculate accuracy on the given test data.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: True labels (n_samples,).

        Returns:
            Accuracy score (fraction of correct predictions).
        """
        predictions = self.predict(X)
        return np.mean(predictions == y)

    def __repr__(self) -> str:
        return (
            f"RandomForestClassifier(n_estimators={self.n_estimators}, "
            f"max_depth={self.max_depth}, max_features='{self.max_features}', "
            f"criterion='{self.criterion}')"
        )


# Need Counter for majority voting in predict
from collections import Counter
