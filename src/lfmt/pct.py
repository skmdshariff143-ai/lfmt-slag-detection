"""
Principal Component Thermography (PCT) Module.

Applies Singular Value Decomposition (SVD) on mean-centered thermogram sequence
to extract spatial Empirical Orthogonal Functions (EOFs) and statistical modes.
Includes both ground-truth-guided and blind component selection strategies.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
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

    def __init__(self, n_components: int = 6, selection_criterion: str = "contrast"):
        self.n_components = n_components
        self.selection_criterion = selection_criterion

    def process(
        self,
        thermograms: np.ndarray,
        ground_truth_mask: Optional[np.ndarray] = None
    ) -> PCTResult:
        """
        Compute PCT EOF spatial modes.

        Args:
            thermograms: 3D array (n_frames, H, W).
            ground_truth_mask: Optional 2D boolean mask (H, W) for ground-truth-guided selection.

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

        # 4. Objective component selection
        best_idx, method_used = self._select_best_component(
            eof_images,
            ground_truth_mask=ground_truth_mask,
            criterion=self.selection_criterion
        )

        selected_image = eof_images[best_idx]
        
        # Ensure defect polarity is positive if ground truth is available
        if ground_truth_mask is not None and np.any(ground_truth_mask):
            defect_mean = np.mean(selected_image[ground_truth_mask])
            sound_mean = np.mean(selected_image[~ground_truth_mask])
            if defect_mean < sound_mean:
                # Invert image so defect appears as positive contrast
                selected_image = -selected_image
                eof_images[best_idx] = selected_image

        elapsed = time.perf_counter() - start_t

        metadata = {
            "n_components_requested": self.n_components,
            "n_components_computed": n_comp,
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

    def _select_best_component(
        self,
        eof_images: np.ndarray,
        ground_truth_mask: Optional[np.ndarray],
        criterion: str
    ) -> Tuple[int, str]:
        """
        Objective selection of the EOF component with highest defect visibility.
        """
        n_comp = eof_images.shape[0]

        # Case A: Ground-truth guided research selection (Contrast or CNR)
        if ground_truth_mask is not None and np.any(ground_truth_mask) and np.any(~ground_truth_mask):
            scores = []
            for i in range(n_comp):
                img = eof_images[i]
                mu_d = np.mean(img[ground_truth_mask])
                mu_s = np.mean(img[~ground_truth_mask])
                var_d = np.var(img[ground_truth_mask])
                var_s = np.var(img[~ground_truth_mask])

                if criterion == "snr" or criterion == "cnr":
                    denom = np.sqrt(var_d + var_s) + 1e-12
                    score = abs(mu_d - mu_s) / denom
                else:  # "contrast"
                    score = abs(mu_d - mu_s)
                scores.append(score)

            best_idx = int(np.argmax(scores))
            return best_idx, f"ground_truth_{criterion}"

        # Case B: Blind selection without ground truth (Kurtosis / Sparsity of spatial anomaly)
        # Anomalies produce heavy tails / high excess kurtosis in spatial intensity distribution
        kurtosis_scores = []
        for i in range(n_comp):
            img = eof_images[i]
            norm_img = (img - np.mean(img)) / (np.std(img) + 1e-12)
            # 4th moment (kurtosis)
            kurt = np.mean(norm_img ** 4) - 3.0
            kurtosis_scores.append(abs(kurt))

        best_idx = int(np.argmax(kurtosis_scores))
        return best_idx, "blind_excess_kurtosis"
