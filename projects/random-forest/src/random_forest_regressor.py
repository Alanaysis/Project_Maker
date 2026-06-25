"""
Random Forest Regressor - An ensemble of regression decision trees using bagging.

This module implements a Random Forest regressor that:
1. Creates multiple bootstrap samples (bagging) from the training data
2. Trains a regression decision tree on each bootstrap sample
3. At each split, randomly selects a subset of features
4. Combines predictions by averaging (instead of voting)

Key differences from classification:
- Uses variance reduction (MSE) as the splitting criterion instead of Gini/Entropy
- Leaf nodes store the mean value of training samples instead of class labels
- Final prediction is the average of all tree predictions
"""

import numpy as np
from typing import Optional, List, Any, Tuple


class Node:
    """A node in the regression decision tree.

    Attributes:
        feature_index: Index of the feature used for splitting (None for leaf)
        threshold: Threshold value for the split (None for leaf)
        left: Left child node (samples <= threshold)
        right: Right child node (samples > threshold)
        value: Predicted value (mean of training samples, only for leaf nodes)
        samples: Number of training samples that reached this node
        impurity: MSE impurity at this node
    """

    def __init__(
        self,
        feature_index: Optional[int] = None,
        threshold: Optional[float] = None,
        left: Optional["Node"] = None,
        right: Optional["Node"] = None,
        value: Optional[float] = None,
        samples: int = 0,
        impurity: float = 0.0,
    ):
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value  # Only set for leaf nodes (mean of y)
        self.samples = samples
        self.impurity = impurity

    @property
    def is_leaf(self) -> bool:
        """Check if this node is a leaf node."""
        return self.value is not None


class DecisionTreeRegressor:
    """A CART decision tree regressor.

    This implementation builds a binary regression tree by recursively finding
    the best feature and threshold to split the data, minimizing the
    mean squared error (MSE) at each node.

    Parameters:
        max_depth: Maximum depth of the tree. None means unlimited.
        min_samples_split: Minimum number of samples required to split a node.
        min_samples_leaf: Minimum number of samples required at a leaf node.
        max_features: Number of features to consider when looking for the best split.
        random_state: Random seed for reproducibility.
    """

    def __init__(
        self,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Optional[Any] = None,
        random_state: Optional[int] = None,
    ):
        if min_samples_split < 2:
            raise ValueError("min_samples_split must be at least 2")
        if min_samples_leaf < 1:
            raise ValueError("min_samples_leaf must be at least 1")

        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.random_state = random_state

        self.root_: Optional[Node] = None
        self.n_features_: int = 0
        self.feature_importances_: Optional[np.ndarray] = None

        self._rng = np.random.RandomState(random_state)

    def _mse(self, y: np.ndarray) -> float:
        """Calculate mean squared error (variance) of a node.

        MSE = (1/n) * sum((y_i - mean(y))^2)

        This is the impurity measure for regression trees. A node with
        low MSE has samples with similar target values (pure node).

        Args:
            y: Array of target values.

        Returns:
            MSE value (0 = all values identical).
        """
        if len(y) == 0:
            return 0.0
        mean_y = np.mean(y)
        return np.mean((y - mean_y) ** 2)

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
        """Find the best split that minimizes MSE.

        For each feature, try all unique values as thresholds and pick the
        one that gives the largest MSE reduction (information gain).

        The MSE reduction is computed as:
            gain = MSE(parent) - (n_left/n)*MSE(left) - (n_right/n)*MSE(right)

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target values (n_samples,).
            feature_indices: Indices of features to consider.

        Returns:
            Tuple of (best_feature_index, best_threshold, best_gain).
            Returns (None, None, 0.0) if no valid split is found.
        """
        best_gain = 0.0
        best_feature = None
        best_threshold = None

        parent_mse = self._mse(y)
        n = len(y)

        for feature_idx in feature_indices:
            # Get unique values for this feature as candidate thresholds
            values = np.unique(X[:, feature_idx])

            # Use midpoints between consecutive unique values as thresholds
            thresholds = (values[:-1] + values[1:]) / 2.0

            for threshold in thresholds:
                left_mask = X[:, feature_idx] <= threshold
                right_mask = ~left_mask

                n_left = np.sum(left_mask)
                n_right = np.sum(right_mask)

                # Skip if split doesn't meet min_samples_leaf
                if n_left < self.min_samples_leaf or n_right < self.min_samples_leaf:
                    continue

                # Compute weighted child MSE
                left_mse = self._mse(y[left_mask])
                right_mse = self._mse(y[right_mask])
                weighted_child_mse = (n_left / n) * left_mse + (n_right / n) * right_mse

                # MSE reduction (information gain)
                gain = parent_mse - weighted_child_mse

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _build_tree(
        self, X: np.ndarray, y: np.ndarray, depth: int = 0
    ) -> Node:
        """Recursively build the regression tree.

        At each node:
        1. Check stopping criteria (max depth, min samples, pure node)
        2. Select a random subset of features
        3. Find the best split among those features
        4. Split the data and recurse

        Leaf nodes store the mean of the target values.

        Args:
            X: Feature matrix for current node.
            y: Target values for current node.
            depth: Current depth in the tree.

        Returns:
            The root Node of the (sub)tree.
        """
        n_samples, n_features = X.shape
        impurity = self._mse(y)
        mean_value = np.mean(y)

        # Check stopping criteria
        is_pure = impurity == 0.0  # All values identical
        max_depth_reached = self.max_depth is not None and depth >= self.max_depth
        too_few_samples = n_samples < self.min_samples_split

        if is_pure or max_depth_reached or too_few_samples:
            return Node(
                value=mean_value,
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
                value=mean_value,
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
        """Recursively compute feature importances based on MSE reduction.

        Importance = sum over all nodes using feature f of:
            n_samples_at_node * (MSE_before - weighted_MSE_after)

        This measures how much each feature reduces the prediction error.

        Args:
            node: Current node to process.
            importances: Array to accumulate importances into.
        """
        if node.is_leaf or node.feature_index is None:
            return

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

    def fit(self, X: np.ndarray, y: np.ndarray) -> "DecisionTreeRegressor":
        """Build the regression tree from training data.

        Args:
            X: Training feature matrix (n_samples, n_features).
            y: Target values (n_samples,).

        Returns:
            self: The fitted regressor.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if len(X) != len(y):
            raise ValueError("X and y must have the same number of samples")

        self.n_features_ = X.shape[1]

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

    def _predict_single(self, x: np.ndarray, node: Node) -> float:
        """Predict the value for a single sample.

        Args:
            x: Feature vector for one sample.
            node: Current node in the tree.

        Returns:
            Predicted value (mean of training samples at the leaf).
        """
        if node.is_leaf:
            return node.value

        if x[node.feature_index] <= node.threshold:
            return self._predict_single(x, node.left)
        else:
            return self._predict_single(x, node.right)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict values for samples in X.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of predicted values.
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

    def get_depth(self) -> int:
        """Get the depth of the tree."""

        def _depth(node: Node) -> int:
            if node.is_leaf:
                return 0
            return 1 + max(_depth(node.left), _depth(node.right))

        if self.root_ is None:
            return 0
        return _depth(self.root_)

    def get_n_leaves(self) -> int:
        """Get the number of leaf nodes."""

        def _count_leaves(node: Node) -> int:
            if node.is_leaf:
                return 1
            return _count_leaves(node.left) + _count_leaves(node.right)

        if self.root_ is None:
            return 0
        return _count_leaves(self.root_)

    def __repr__(self) -> str:
        return (
            f"DecisionTreeRegressor(max_depth={self.max_depth}, "
            f"min_samples_split={self.min_samples_split})"
        )


class RandomForestRegressor:
    """A Random Forest regressor.

    This implements the Random Forest algorithm for regression:

    For each tree (n_estimators times):
        1. Bootstrap: Draw a random sample with replacement from the training data
        2. Train: Build a regression tree on the bootstrap sample
           - At each node, randomly select max_features features to consider
           - Find the best split that minimizes MSE
        3. Store the trained tree

    For prediction:
        - Each tree predicts independently
        - Final prediction is the AVERAGE of all tree predictions

    Parameters:
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
        min_samples_split: Minimum samples to split a node.
        min_samples_leaf: Minimum samples at a leaf node.
        max_features: Number of features to consider at each split.
        bootstrap: Whether to use bootstrap sampling.
        random_state: Random seed for reproducibility.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Any = "sqrt",
        bootstrap: bool = True,
        random_state: Optional[int] = None,
    ):
        if n_estimators < 1:
            raise ValueError("n_estimators must be at least 1")

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state

        self.trees_: List[DecisionTreeRegressor] = []
        self.n_features_: int = 0
        self.feature_importances_: Optional[np.ndarray] = None
        self.oob_score_: Optional[float] = None

        self._rng = np.random.RandomState(random_state)

    def _bootstrap_sample(
        self, X: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create a bootstrap sample of the training data.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target values (n_samples,).

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

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestRegressor":
        """Build the random forest from training data.

        Args:
            X: Training feature matrix (n_samples, n_features).
            y: Target values (n_samples,).

        Returns:
            self: The fitted regressor.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)

        if X.ndim == 1:
            X = X.reshape(-1, 1)

        if len(X) != len(y):
            raise ValueError("X and y must have the same number of samples")

        self.n_features_ = X.shape[1]
        self.trees_ = []

        # Track OOB predictions for OOB score calculation
        if self.bootstrap:
            oob_predictions = np.zeros(len(X))
            oob_counts = np.zeros(len(X))

        for i in range(self.n_estimators):
            tree_seed = self._rng.randint(0, 2**31)

            # Create bootstrap sample or use full dataset
            if self.bootstrap:
                X_sample, y_sample, oob_indices = self._bootstrap_sample(X, y)
            else:
                X_sample, y_sample = X, y
                oob_indices = np.array([])

            # Create and train a regression tree
            tree = DecisionTreeRegressor(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features=self.max_features,
                random_state=tree_seed,
            )
            tree.fit(X_sample, y_sample)
            self.trees_.append(tree)

            # Accumulate OOB predictions
            if self.bootstrap and len(oob_indices) > 0:
                oob_preds = tree.predict(X[oob_indices])
                for idx, pred in zip(oob_indices, oob_preds):
                    oob_predictions[idx] += pred
                    oob_counts[idx] += 1

        # Compute feature importances (average across all trees)
        self.feature_importances_ = np.zeros(self.n_features_)
        for tree in self.trees_:
            if tree.feature_importances_ is not None:
                self.feature_importances_ += tree.feature_importances_
        self.feature_importances_ /= self.n_estimators

        # Compute OOB score (R^2 on OOB samples)
        if self.bootstrap:
            oob_mask = oob_counts > 0
            if np.any(oob_mask):
                oob_pred_values = oob_predictions[oob_mask] / oob_counts[oob_mask]
                y_oob = y[oob_mask]

                # R^2 = 1 - SS_res / SS_tot
                ss_res = np.sum((y_oob - oob_pred_values) ** 2)
                ss_tot = np.sum((y_oob - np.mean(y_oob)) ** 2)
                self.oob_score_ = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            else:
                self.oob_score_ = None

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict values by averaging all tree predictions.

        Each tree in the forest predicts independently. The final prediction
        is the arithmetic mean of all tree predictions.

        Averaging reduces variance: individual trees may overfit or underfit,
        but the average tends to be more stable and accurate.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of predicted values (averaged across all trees).
        """
        if not self.trees_:
            raise RuntimeError("Forest has not been fitted. Call fit() first.")

        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            if self.n_features_ == 1:
                X = X.reshape(-1, 1)
            else:
                X = X.reshape(1, -1)

        # Collect predictions from all trees
        # Shape: (n_estimators, n_samples)
        all_predictions = np.array([tree.predict(X) for tree in self.trees_])

        # Average predictions across all trees
        return np.mean(all_predictions, axis=0)

    def __repr__(self) -> str:
        return (
            f"RandomForestRegressor(n_estimators={self.n_estimators}, "
            f"max_depth={self.max_depth}, max_features='{self.max_features}')"
        )
