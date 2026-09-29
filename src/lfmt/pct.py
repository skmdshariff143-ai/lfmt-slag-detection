"""
Principal Component Thermography (PCT) Module.

Applies Singular Value Decomposition (SVD) on mean-centered thermogram sequence
to extract spatial Empirical Orthogonal Functions (EOFs) and statistical modes.
Includes both ground-truth-guided and blind component selection strategies.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np
from sklearn.decomposition import TruncatedSVD


@dataclass
class PCTResult:
    """
    Principal Component Thermography Output.

    Attributes:
        eof_images: 3D array of spatial component images (n_components, H, W).
        temporal_scores: 2D array of temporal projection scores (n_frames, n_components).
        singular_values: 1D array of singular values for each component.
        explained_variance_ratio: 1D array of explained variance fraction per component.
        cumulative_variance_ratio: 1D array of cumulative explained variance.
        selected_component_idx: 0-indexed integer of the best defect-isolating component.
        selected_eof_image: 2D array (H, W) of the optimal EOF image.
        selection_method: Strategy used to select best component ("contrast", "snr", "blind_kurtosis").
        runtime_seconds: Execution time in seconds.
        metadata: Detailed PCT metadata.
    """
    eof_images: np.ndarray
    temporal_scores: np.ndarray
    singular_values: np.ndarray
    explained_variance_ratio: np.ndarray
    cumulative_variance_ratio: np.ndarray
    selected_component_idx: int
    selected_eof_image: np.ndarray
    selection_method: str
    runtime_seconds: float
    metadata: Dict[str, Any]


class PrincipalComponentThermography:
    """
    PCT Engine using Singular Value Decomposition.
    """

    def __init__(
        self,
        n_components: int = 6,
        selection_criterion: str = "blind_kurtosis",
        mode: str = "blind"
    ):
        self.n_components = n_components
        self.selection_criterion = selection_criterion
        self.mode = mode.lower().strip()  # "blind" or "oracle"

    def process(
        self,
        thermograms: np.ndarray,
        ground_truth_mask: Optional[np.ndarray] = None
    ) -> PCTResult:
        """
        Compute PCT EOF spatial modes.

        Args:
            thermograms: 3D array (n_frames, H, W).
            ground_truth_mask: Optional 2D boolean mask (H, W). ONLY used if mode == 'oracle'.

        Returns:
            PCTResult container.
        """
        start_t = time.perf_counter()
        n_frames, H, W = thermograms.shape
        n_comp = min(self.n_components, n_frames, H * W)

        # 1. Unfold 3D tensor to 2D matrix (time, pixels)
        A = thermograms.reshape(n_frames, H * W).astype(np.float64)

        # 2. Mean-center along time axis (standard PCT preprocessing)
        mean_profile = np.mean(A, axis=0, keepdims=True)
        A_centered = A - mean_profile

        # 3. Compute SVD
        svd = TruncatedSVD(n_components=n_comp, algorithm="randomized", random_state=42)
        temporal_scores = svd.fit_transform(A_centered)  # shape: (n_frames, n_comp)
        
        # EOF spatial components: rows of svd.components_
        eof_raw = svd.components_  # shape: (n_comp, H * W)
        eof_images = eof_raw.reshape(n_comp, H, W)

        # Variance ratios
        exp_var = svd.explained_variance_ratio_
        cum_var = np.cumsum(exp_var)
        sing_vals = svd.singular_values_

        # 4. Component selection
        use_oracle = (self.mode == "oracle" or self.selection_criterion in ("contrast", "snr", "oracle")) and (ground_truth_mask is not None and np.any(ground_truth_mask))
        if use_oracle:
            best_idx, method_used = self._select_best_component_oracle(
                eof_images, ground_truth_mask, criterion=self.selection_criterion
            )
            selected_image = eof_images[best_idx]
            defect_mean = np.mean(selected_image[ground_truth_mask])
            sound_mean = np.mean(selected_image[~ground_truth_mask])
            if defect_mean < sound_mean:
                selected_image = -selected_image
                eof_images[best_idx] = selected_image
        else:
            best_idx, method_used = self._select_best_component_blind(eof_images)
            selected_image = eof_images[best_idx]
            # Blind polarity correction: align with positive spatial skewness (localized anomaly)
            img_norm = (selected_image - np.mean(selected_image)) / (np.std(selected_image) + 1e-12)
            skewness = float(np.mean(img_norm ** 3))
            if skewness < 0:
                selected_image = -selected_image
                eof_images[best_idx] = selected_image

        elapsed = time.perf_counter() - start_t

        metadata = {
            "n_components_requested": self.n_components,
            "n_components_computed": n_comp,
            "selection_mode": self.mode,
            "selection_method": method_used,
            "selected_component": best_idx + 1,  # 1-indexed for display
            "runtime_s": elapsed,
        }

        return PCTResult(
            eof_images=eof_images,
            temporal_scores=temporal_scores,
            singular_values=sing_vals,
            explained_variance_ratio=exp_var,
            cumulative_variance_ratio=cum_var,
            selected_component_idx=best_idx,
            selected_eof_image=selected_image,
            selection_method=method_used,
            runtime_seconds=elapsed,
            metadata=metadata
        )

    def _select_best_component_blind(self, eof_images: np.ndarray) -> Tuple[int, str]:
        """Blind selection via excess spatial kurtosis."""
        n_comp = eof_images.shape[0]
        kurtosis_scores = []
        for i in range(n_comp):
            img = eof_images[i]
            norm_img = (img - np.mean(img)) / (np.std(img) + 1e-12)
            kurt = np.mean(norm_img ** 4) - 3.0
            kurtosis_scores.append(abs(kurt))

        best_idx = int(np.argmax(kurtosis_scores))
        return best_idx, "blind_excess_kurtosis"

    def _select_best_component_oracle(
        self,
        eof_images: np.ndarray,
        ground_truth_mask: np.ndarray,
        criterion: str
    ) -> Tuple[int, str]:
        """Oracle selection with ground truth for academic benchmark comparison."""
        n_comp = eof_images.shape[0]
        scores = []
        for i in range(n_comp):
            img = eof_images[i]
            mu_d = np.mean(img[ground_truth_mask])
            mu_s = np.mean(img[~ground_truth_mask])
            var_d = np.var(img[ground_truth_mask])
            var_s = np.var(img[~ground_truth_mask])

            if criterion in ("snr", "cnr"):
                denom = np.sqrt(var_d + var_s) + 1e-12
                score = abs(mu_d - mu_s) / denom
            else:
                score = abs(mu_d - mu_s)
            scores.append(score)

        best_idx = int(np.argmax(scores))
        return best_idx, f"ground_truth_{criterion}"

