"""
Decision Tree Classifier - A CART (Classification and Regression Tree) implementation.

This module provides a decision tree classifier that supports:
- Gini impurity and entropy as splitting criteria
- Maximum depth control
- Minimum samples split/leaf constraints
- Feature subsampling (used by Random Forest)

The tree is built recursively by finding the best split at each node
based on information gain.
"""

import numpy as np
from collections import Counter
from typing import Optional, List, Tuple, Any


class Node:
    """A node in the decision tree.

    Attributes:
        feature_index: Index of the feature used for splitting (None for leaf nodes)
        threshold: Threshold value for the split (None for leaf nodes)
        left: Left child node (samples <= threshold)
        right: Right child node (samples > threshold)
        value: Predicted class label (only for leaf nodes)
        samples: Number of training samples that reached this node
        impurity: Impurity measure at this node
    """

    def __init__(
        self,
        feature_index: Optional[int] = None,
        threshold: Optional[float] = None,
        left: Optional["Node"] = None,
        right: Optional["Node"] = None,
        value: Optional[Any] = None,
        samples: int = 0,
        impurity: float = 0.0,
    ):
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value  # Only set for leaf nodes
        self.samples = samples
        self.impurity = impurity

    @property
    def is_leaf(self) -> bool:
        """Check if this node is a leaf node."""
        return self.value is not None


class DecisionTreeClassifier:
    """A CART decision tree classifier.

    This implementation builds a binary decision tree by recursively finding
    the best feature and threshold to split the data, optimizing for either
    Gini impurity or entropy.

    Parameters:
        max_depth: Maximum depth of the tree. None means unlimited.
        min_samples_split: Minimum number of samples required to split a node.
        min_samples_leaf: Minimum number of samples required at a leaf node.
        criterion: The function to measure split quality ('gini' or 'entropy').
        max_features: Number of features to consider when looking for the best split.
            If None, all features are considered. If int, that many features are
            randomly selected at each split. If float, it represents a fraction.
        random_state: Random seed for reproducibility.
    """

    CRITERIA = {"gini", "entropy"}

    def __init__(
        self,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        criterion: str = "gini",
        max_features: Optional[Any] = None,
        random_state: Optional[int] = None,
    ):
        if criterion not in self.CRITERIA:
            raise ValueError(
                f"Criterion must be one of {self.CRITERIA}, got '{criterion}'"
            )
        if min_samples_split < 2:
            raise ValueError("min_samples_split must be at least 2")
        if min_samples_leaf < 1:
            raise ValueError("min_samples_leaf must be at least 1")

        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.criterion = criterion
        self.max_features = max_features
        self.random_state = random_state

        self.root_: Optional[Node] = None
        self.n_features_: int = 0
        self.n_classes_: int = 0
        self.classes_: np.ndarray = np.array([])
        self.feature_importances_: Optional[np.ndarray] = None

        self._rng = np.random.RandomState(random_state)

    def _gini(self, y: np.ndarray) -> float:
        """Calculate Gini impurity.

        Gini = 1 - sum(p_i^2) where p_i is the proportion of class i.

        Args:
            y: Array of class labels.

        Returns:
            Gini impurity value (0 = pure, max = 1 - 1/n_classes).
        """
        if len(y) == 0:
            return 0.0
        counts = np.bincount(y.astype(int))
        probabilities = counts / len(y)
        return 1.0 - np.sum(probabilities ** 2)

    def _entropy(self, y: np.ndarray) -> float:
        """Calculate entropy.

        Entropy = -sum(p_i * log2(p_i)) where p_i is the proportion of class i.

        Args:
            y: Array of class labels.

        Returns:
            Entropy value (0 = pure).
        """
        if len(y) == 0:
            return 0.0
        counts = np.bincount(y.astype(int))
        probabilities = counts / len(y)
        # Filter out zero probabilities to avoid log(0)
        probabilities = probabilities[probabilities > 0]
        return -np.sum(probabilities * np.log2(probabilities))

    def _impurity(self, y: np.ndarray) -> float:
        """Calculate impurity using the chosen criterion."""
        if self.criterion == "gini":
            return self._gini(y)
        else:
            return self._entropy(y)

    def _information_gain(
        self, y: np.ndarray, left_y: np.ndarray, right_y: np.ndarray
    ) -> float:
        """Calculate information gain from a split.

        IG = impurity(parent) - weighted_avg(impurity(left), impurity(right))

        Args:
            y: Parent node labels.
            left_y: Left child labels.
            right_y: Right child labels.

        Returns:
            Information gain value (higher is better).
        """
        n = len(y)
        if n == 0:
            return 0.0

        parent_impurity = self._impurity(y)
        left_weight = len(left_y) / n
        right_weight = len(right_y) / n

        child_impurity = (
            left_weight * self._impurity(left_y)
            + right_weight * self._impurity(right_y)
        )

        return parent_impurity - child_impurity

    def _get_max_features(self, n_features: int) -> int:
        """Calculate the actual number of features to consider.

        Args:
            n_features: Total number of available features.

        Returns:
            Number of features to consider for each split.
        """
        if self.max_features is None:
            return n_features
        elif isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        elif isinstance(self.max_features, float):
            return max(1, int(self.max_features * n_features))
        elif self.max_features == "sqrt":
            return max(1, int(np.sqrt(n_features)))
        elif self.max_features == "log2":
            return max(1, int(np.log2(n_features)))
        else:
            raise ValueError(f"Invalid max_features: {self.max_features}")

    def _select_features(self, n_features: int) -> np.ndarray:
        """Randomly select a subset of features.

        Args:
            n_features: Total number of features.

        Returns:
            Array of selected feature indices.
        """
        n_selected = self._get_max_features(n_features)
        return self._rng.choice(n_features, size=n_selected, replace=False)

    def _find_best_split(
        self, X: np.ndarray, y: np.ndarray, feature_indices: np.ndarray
    ) -> Tuple[Optional[int], Optional[float], float]:
        """Find the best split among the given features.

        For each feature, try all unique values as thresholds and pick the
        one that maximizes information gain.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target labels (n_samples,).
            feature_indices: Indices of features to consider.

        Returns:
            Tuple of (best_feature_index, best_threshold, best_gain).
            Returns (None, None, 0.0) if no valid split is found.
        """
        best_gain = 0.0
        best_feature = None
        best_threshold = None

        for feature_idx in feature_indices:
            # Get unique values for this feature as candidate thresholds
            values = np.unique(X[:, feature_idx])

            # Use midpoints between consecutive unique values as thresholds
            thresholds = (values[:-1] + values[1:]) / 2.0

            for threshold in thresholds:
                left_mask = X[:, feature_idx] <= threshold
                right_mask = ~left_mask

                # Skip if split doesn't meet min_samples_leaf
                if (
                    np.sum(left_mask) < self.min_samples_leaf
                    or np.sum(right_mask) < self.min_samples_leaf
                ):
                    continue

                gain = self._information_gain(y, y[left_mask], y[right_mask])

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _build_tree(
        self, X: np.ndarray, y: np.ndarray, depth: int = 0
    ) -> Node:
        """Recursively build the decision tree.

        Args:
            X: Feature matrix for current node.
            y: Target labels for current node.
            depth: Current depth in the tree.

        Returns:
            The root Node of the (sub)tree.
        """
        n_samples, n_features = X.shape
        impurity = self._impurity(y)

        # Count class occurrences
        class_counts = Counter(y)
        majority_class = class_counts.most_common(1)[0][0]

        # Check stopping criteria
        is_pure = len(class_counts) == 1
        max_depth_reached = self.max_depth is not None and depth >= self.max_depth
        too_few_samples = n_samples < self.min_samples_split

        if is_pure or max_depth_reached or too_few_samples:
            return Node(
                value=majority_class,
                samples=n_samples,
                impurity=impurity,
            )

        # Select random subset of features (key for Random Forest)
        selected_features = self._select_features(n_features)

        # Find the best split
        best_feature, best_threshold, best_gain = self._find_best_split(
            X, y, selected_features
        )

        # If no valid split found, create a leaf
        if best_feature is None or best_gain <= 0:
            return Node(
                value=majority_class,
                samples=n_samples,
                impurity=impurity,
            )

        # Split the data
        left_mask = X[:, best_feature] <= best_threshold
        right_mask = ~left_mask

        # Recursively build left and right subtrees
        left_subtree = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_subtree = self._build_tree(X[right_mask], y[right_mask], depth + 1)

        return Node(
            feature_index=best_feature,
            threshold=best_threshold,
            left=left_subtree,
            right=right_subtree,
            samples=n_samples,
            impurity=impurity,
        )

    def _compute_feature_importances(self, node: Node, importances: np.ndarray):
        """Recursively compute feature importances.

        Importance is based on the total reduction in impurity brought by each feature,
        weighted by the number of samples that pass through each node.

        Args:
            node: Current node to process.
            importances: Array to accumulate importances into.
        """
        if node.is_leaf or node.feature_index is None:
            return

        # Weighted impurity reduction at this node
        n = node.samples
        left_n = node.left.samples if node.left else 0
        right_n = node.right.samples if node.right else 0

        weighted_child_impurity = (
            (left_n / n) * (node.left.impurity if node.left else 0)
            + (right_n / n) * (node.right.impurity if node.right else 0)
        )

        importance = n * (node.impurity - weighted_child_impurity)
        importances[node.feature_index] += importance

        # Recurse into children
        self._compute_feature_importances(node.left, importances)
        self._compute_feature_importances(node.right, importances)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "DecisionTreeClassifier":
        """Build the decision tree from training data.

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

        # Build the tree
        self.root_ = self._build_tree(X, y)

        # Compute feature importances
        self.feature_importances_ = np.zeros(self.n_features_)
        self._compute_feature_importances(self.root_, self.feature_importances_)

        # Normalize importances
        total = np.sum(self.feature_importances_)
        if total > 0:
            self.feature_importances_ /= total

        return self

    def _predict_single(self, x: np.ndarray, node: Node) -> Any:
        """Predict the class for a single sample.

        Args:
            x: Feature vector for one sample.
            node: Current node in the tree.

        Returns:
            Predicted class label.
        """
        if node.is_leaf:
            return node.value

        if x[node.feature_index] <= node.threshold:
            return self._predict_single(x, node.left)
        else:
            return self._predict_single(x, node.right)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels for samples in X.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of predicted class labels.
        """
        if self.root_ is None:
            raise RuntimeError("Tree has not been fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            if self.n_features_ == 1:
                X = X.reshape(-1, 1)
            else:
                X = X.reshape(1, -1)

        return np.array([self._predict_single(x, self.root_) for x in X])

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

    def get_depth(self) -> int:
        """Get the depth of the tree.

        Returns:
            Maximum depth of the tree.
        """

        def _depth(node: Node) -> int:
            if node.is_leaf:
                return 0
            return 1 + max(_depth(node.left), _depth(node.right))

        if self.root_ is None:
            return 0
        return _depth(self.root_)

    def get_n_leaves(self) -> int:
        """Get the number of leaf nodes.

        Returns:
            Number of leaf nodes in the tree.
        """

        def _count_leaves(node: Node) -> int:
            if node.is_leaf:
                return 1
            return _count_leaves(node.left) + _count_leaves(node.right)

        if self.root_ is None:
            return 0
        return _count_leaves(self.root_)

    def __repr__(self) -> str:
        return (
            f"DecisionTreeClassifier(max_depth={self.max_depth}, "
            f"min_samples_split={self.min_samples_split}, "
            f"criterion='{self.criterion}')"
        )
