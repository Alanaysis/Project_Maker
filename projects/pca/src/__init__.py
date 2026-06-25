"""PCA (Principal Component Analysis) - 从零实现主成分分析降维算法"""

from .pca import PCA
from .kernel_pca import KernelPCA
from .incremental_pca import IncrementalPCA
from .covariance import compute_covariance_matrix
from .eigen import eigen_decomposition
from .visualization import plot_pca_2d, plot_pca_3d, plot_explained_variance

__version__ = "1.0.0"
__all__ = [
    "PCA",
    "KernelPCA",
    "IncrementalPCA",
    "compute_covariance_matrix",
    "eigen_decomposition",
    "plot_pca_2d",
    "plot_pca_3d",
    "plot_explained_variance",
]
