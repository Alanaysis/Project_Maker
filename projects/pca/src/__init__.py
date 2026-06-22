"""PCA (Principal Component Analysis) - 从零实现主成分分析降维算法"""

from .pca import PCA
from .covariance import compute_covariance_matrix
from .eigen import eigen_decomposition
from .visualization import plot_pca_2d, plot_pca_3d, plot_explained_variance

__version__ = "1.0.0"
__all__ = [
    "PCA",
    "compute_covariance_matrix",
    "eigen_decomposition",
    "plot_pca_2d",
    "plot_pca_3d",
    "plot_explained_variance",
]
