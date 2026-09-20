r"""
Random Projection Technique (RPT) Module for Thermography.

Embeds high-dimensional thermal transient curves into a lower-dimensional subspace
using Gaussian or Sparse random projections while preserving pairwise Euclidean distances
according to the Johnson-Lindenstrauss lemma:
    (1 - \epsilon) \|u - v\|^2 \le \|\Phi u - \Phi v\|^2 \le (1 + \epsilon) \|u - v\|^2
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np
from sklearn.random_projection import GaussianRandomProjection, SparseRandomProjection


@dataclass
class RPTResult:
    """
    Random Projection Technique Output.

    Attributes:
        projected_components: 3D array of projected spatial feature maps (n_components, H, W).
        projected_matrix: 2D array of projected data (n_components, H * W).
        selected_component_idx: Optimal defect-isolating projected feature index.
        selected_rpt_image: 2D array (H, W) of optimal RPT anomaly map.
        compression_ratio: Dimension reduction ratio (n_frames / n_components).
        matrix_type: Random projection matrix type ("gaussian" or "sparse").
        runtime_seconds: Execution time in seconds.
        metadata: Detailed solver metadata.
    """
    projected_components: np.ndarray
    projected_matrix: np.ndarray
    selected_component_idx: int
    selected_rpt_image: np.ndarray
    compression_ratio: float
    matrix_type: str
    runtime_seconds: float
    metadata: Dict[str, Any]


class RandomProjectionTechnique:
    """
    RPT Engine using Gaussian or Sparse Random Projections.
    """

    def __init__(
        self,
        n_components: int = 6,
        matrix_type: str = "gaussian",
        random_state: int = 42,
        mode: str = "blind"
    ):
        self.n_components = n_components
        self.matrix_type = matrix_type.lower().strip()
        self.random_state = random_state
        self.mode = mode.lower().strip()

    def process(
        self,
        thermograms: np.ndarray,
        ground_truth_mask: Optional[np.ndarray] = None
    ) -> RPTResult:
        """
        Execute random projection on thermogram sequence.

        Args:
            thermograms: 3D array (n_frames, H, W).
            ground_truth_mask: Optional 2D boolean mask. ONLY used if mode == 'oracle'.

        Returns:
            RPTResult object.
        """
        start_t = time.perf_counter()
        n_frames, H, W = thermograms.shape
        n_comp = min(self.n_components, n_frames - 1, H * W)

        # 1. Unfold 3D tensor to (n_pixels, n_frames) for projection across temporal features
        A_pixels = thermograms.reshape(n_frames, H * W).T  # shape: (n_pixels, n_frames)

        # Mean-center temporal curves
        A_centered = A_pixels - np.mean(A_pixels, axis=1, keepdims=True)

        # 2. Random projection
        if self.matrix_type == "sparse":
            transformer = SparseRandomProjection(
                n_components=n_comp,
                random_state=self.random_state
            )
        else:
            transformer = GaussianRandomProjection(
                n_components=n_comp,
                random_state=self.random_state
            )

        # Projected features: shape (n_pixels, n_comp)
        projected = transformer.fit_transform(A_centered)

        # Reshape projected components to (n_comp, H, W)
        projected_T = projected.T  # (n_comp, n_pixels)
        proj_images = projected_T.reshape(n_comp, H, W)

        # 3. Component selection and polarity
        if self.mode == "oracle" and ground_truth_mask is not None and np.any(ground_truth_mask):
            best_idx = self._select_best_component_oracle(proj_images, ground_truth_mask)
            selected_image = proj_images[best_idx]
            defect_mean = np.mean(selected_image[ground_truth_mask])
            sound_mean = np.mean(selected_image[~ground_truth_mask])
            if defect_mean < sound_mean:
                selected_image = -selected_image
                proj_images[best_idx] = selected_image
            selection_method = "oracle_contrast"
        else:
            best_idx = self._select_best_component_blind(proj_images)
            selected_image = proj_images[best_idx]
            img_norm = (selected_image - np.mean(selected_image)) / (np.std(selected_image) + 1e-12)
            skewness = float(np.mean(img_norm ** 3))
            if skewness < 0:
                selected_image = -selected_image
                proj_images[best_idx] = selected_image
            selection_method = "blind_dynamic_range"

        elapsed = time.perf_counter() - start_t
        comp_ratio = float(n_frames) / float(n_comp) if n_comp > 0 else 1.0

        metadata = {
            "method": "Random Projection Technique (RPT)",
            "matrix_type": self.matrix_type,
            "original_dim": n_frames,
            "projected_dim": n_comp,
            "compression_ratio": comp_ratio,
            "selection_mode": self.mode,
            "selection_method": selection_method,
            "selected_component": best_idx + 1,
            "runtime_s": elapsed,
        }

        return RPTResult(
            projected_components=proj_images,
            projected_matrix=projected_T,
            selected_component_idx=best_idx,
            selected_rpt_image=selected_image,
            compression_ratio=comp_ratio,
            matrix_type=self.matrix_type,
            runtime_seconds=elapsed,
            metadata=metadata
        )

    def _select_best_component_blind(self, proj_images: np.ndarray) -> int:
        """Blind selection by maximum dynamic range / kurtosis."""
        n_comp = proj_images.shape[0]
        ranges = [np.ptp(proj_images[i]) for i in range(n_comp)]
        return int(np.argmax(ranges))

    def _select_best_component_oracle(
        self,
        proj_images: np.ndarray,
        ground_truth_mask: np.ndarray
    ) -> int:
        """Oracle selection using ground truth contrast."""
        n_comp = proj_images.shape[0]
        contrasts = [
            abs(np.mean(proj_images[i][ground_truth_mask]) - np.mean(proj_images[i][~ground_truth_mask]))
            for i in range(n_comp)
        ]
        return int(np.argmax(contrasts))
