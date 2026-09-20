"""
Sparse Principal Component Thermography (SPCT) Module.

Employs L1-regularized sparse matrix decomposition (SparsePCA) to isolate localized
thermal anomalies while enforcing spatial sparsity across the EOF basis functions.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np
from sklearn.decomposition import SparsePCA, MiniBatchSparsePCA

from lfmt.config import SPCTConfig


@dataclass
class SPCTResult:
    """
    Sparse Principal Component Thermography Output.

    Attributes:
        sparse_components: 3D array of sparse spatial component images (n_components, H, W).
        transformed_scores: 2D array of projected temporal scores (n_frames, n_components).
        non_zero_ratios: 1D array of fraction of non-zero coefficients per component.
        selected_component_idx: Best defect-isolating component index.
        selected_sparse_image: 2D array (H, W) of the optimal sparse component.
        sparsity_alpha: L1 regularization strength parameter.
        runtime_seconds: Elapsed processing time in seconds.
        metadata: SPCT solver metadata.
    """
    sparse_components: np.ndarray
    transformed_scores: np.ndarray
    non_zero_ratios: np.ndarray
    selected_component_idx: int
    selected_sparse_image: np.ndarray
    sparsity_alpha: float
    runtime_seconds: float
    metadata: Dict[str, Any]


class SparsePrincipalComponentThermography:
    """
    SPCT Engine utilizing L1-penalized SparsePCA.
    """

    def __init__(
        self,
        n_components: int = 6,
        alpha: float = 0.05,
        max_iter: int = 200,
        random_state: int = 42,
        use_minibatch: bool = False
    ):
        self.n_components = n_components
        self.alpha = alpha
        self.max_iter = max_iter
        self.random_state = random_state
        self.use_minibatch = use_minibatch

    def process(
        self,
        thermograms: np.ndarray,
        ground_truth_mask: Optional[np.ndarray] = None
    ) -> SPCTResult:
        """
        Compute SPCT sparse spatial modes.

        Args:
            thermograms: 3D array of shape (n_frames, H, W).
            ground_truth_mask: Optional 2D boolean mask for ground-truth-guided component selection.

        Returns:
            SPCTResult object.
        """
        start_t = time.perf_counter()
        n_frames, H, W = thermograms.shape
        n_comp = min(self.n_components, n_frames, H * W)

        # 1. Unfold 3D tensor to 2D matrix (time, pixels)
        A = thermograms.reshape(n_frames, H * W).astype(np.float64)

        # 2. Mean-center
        mean_profile = np.mean(A, axis=0, keepdims=True)
        A_centered = A - mean_profile

        # 3. Fit SparsePCA
        if self.use_minibatch:
            spca = MiniBatchSparsePCA(
                n_components=n_comp,
                alpha=self.alpha,
                max_iter=self.max_iter,
                random_state=self.random_state,
                batch_size=min(32, n_frames)
            )
        else:
            spca = SparsePCA(
                n_components=n_comp,
                alpha=self.alpha,
                max_iter=self.max_iter,
                random_state=self.random_state,
                method="cd"
            )

        transformed_scores = spca.fit_transform(A_centered)  # (n_frames, n_comp)
        raw_components = spca.components_                    # (n_comp, H * W)
        sparse_images = raw_components.reshape(n_comp, H, W)

        # 4. Measure sparsity (fraction of non-zero coefficients)
        tol = 1e-6
        non_zero_ratios = np.array([
            float(np.count_nonzero(np.abs(raw_components[i]) > tol)) / float(H * W)
            for i in range(n_comp)
        ])

        # 5. Select best component
        best_idx = self._select_best_component(sparse_images, ground_truth_mask)
        selected_image = sparse_images[best_idx]

        # Polarity correction
        if ground_truth_mask is not None and np.any(ground_truth_mask):
            defect_mean = np.mean(selected_image[ground_truth_mask])
            sound_mean = np.mean(selected_image[~ground_truth_mask])
            if defect_mean < sound_mean:
                selected_image = -selected_image
                sparse_images[best_idx] = selected_image

        elapsed = time.perf_counter() - start_t

        metadata = {
            "method": "Sparse PCA (SPCT)",
            "alpha": self.alpha,
            "max_iter": self.max_iter,
            "n_components": n_comp,
            "use_minibatch": self.use_minibatch,
            "runtime_s": elapsed,
        }

        return SPCTResult(
            sparse_components=sparse_images,
            transformed_scores=transformed_scores,
            non_zero_ratios=non_zero_ratios,
            selected_component_idx=best_idx,
            selected_sparse_image=selected_image,
            sparsity_alpha=self.alpha,
            runtime_seconds=elapsed,
            metadata=metadata
        )

    def _select_best_component(
        self,
        sparse_images: np.ndarray,
        ground_truth_mask: Optional[np.ndarray]
    ) -> int:
        """Select component with strongest defect contrast or highest kurtosis."""
        n_comp = sparse_images.shape[0]

        if ground_truth_mask is not None and np.any(ground_truth_mask) and np.any(~ground_truth_mask):
            contrasts = [
                abs(np.mean(sparse_images[i][ground_truth_mask]) - np.mean(sparse_images[i][~ground_truth_mask]))
                for i in range(n_comp)
            ]
            return int(np.argmax(contrasts))

        # Blind selection by peak-to-background ratio
        scores = []
        for i in range(n_comp):
            img = sparse_images[i]
            scores.append(np.max(np.abs(img)) / (np.std(img) + 1e-12))
        return int(np.argmax(scores))
