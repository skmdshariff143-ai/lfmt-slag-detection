"""
Monte Carlo Dropout Epistemic Uncertainty Estimation Module.

Executes multiple stochastic forward passes with dropout active at inference time
to quantify predictive variance, epistemic uncertainty, and confidence intervals.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import torch
import torch.nn.functional as F

from ml.models.multitask import PhysicsInformedMultiTaskNet, MultiTaskPrediction


@dataclass
class UncertaintyEstimate:
    """Quantified predictive uncertainty metrics."""
    mean_prediction: str
    mean_probability: float
    predictive_variance: float
    predictive_entropy: float
    epistemic_uncertainty: float
    confidence_interval_95: Tuple[float, float]
    mc_samples_count: int
    is_uncertain: bool
    status_label: str  # "HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "LOW_CONFIDENCE", "INSUFFICIENT_EVIDENCE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_prediction": self.mean_prediction,
            "mean_probability": round(self.mean_probability, 4),
            "predictive_variance": round(self.predictive_variance, 4),
            "predictive_entropy": round(self.predictive_entropy, 4),
            "epistemic_uncertainty": round(self.epistemic_uncertainty, 4),
            "confidence_interval_95": [round(self.confidence_interval_95[0], 4), round(self.confidence_interval_95[1], 4)],
            "mc_samples_count": self.mc_samples_count,
            "is_uncertain": self.is_uncertain,
            "status_label": self.status_label
        }


class MCDropoutUncertaintyEstimator:
    """Monte Carlo Dropout Engine."""

    def __init__(self, n_passes: int = 10):
        self.n_passes = n_passes

    def estimate(
        self,
        model: PhysicsInformedMultiTaskNet,
        image_np: np.ndarray,
        physics_vec: Optional[np.ndarray] = None
    ) -> UncertaintyEstimate:
        """Execute N stochastic MC dropout passes to quantify epistemic variance."""
        model.train()  # Activate dropout

        if image_np.ndim == 2:
            image_np = image_np[np.newaxis, np.newaxis, :, :]
        elif image_np.ndim == 3:
            image_np = image_np[np.newaxis, :, :, :]

        img_t = torch.from_numpy(image_np).float()
        phys_t = torch.from_numpy(physics_vec).float().view(1, -1) if physics_vec is not None else torch.zeros((1, 8)).float()
        if phys_t.shape[1] < 8:
            phys_t = F.pad(phys_t, (0, 8 - phys_t.shape[1]))

        probs_list = []
        with torch.no_grad():
            for _ in range(self.n_passes):
                logits, _, _, _, _, _ = model(img_t, phys_t)
                probs = F.softmax(logits, dim=1).numpy()[0]
                probs_list.append(probs)

        probs_arr = np.array(probs_list)  # (N_passes, num_classes)
        mean_probs = np.mean(probs_arr, axis=0)
        var_probs = np.var(probs_arr, axis=0)

        classes = PhysicsInformedMultiTaskNet.CLASS_NAMES
        top_idx = int(np.argmax(mean_probs))
        top_class = classes[top_idx]
        mean_p = float(mean_probs[top_idx])
        pred_var = float(var_probs[top_idx])

        # Predictive entropy H = -sum(p * log(p))
        eps = 1e-12
        entropy = float(-np.sum(mean_probs * np.log(mean_probs + eps)))
        epistemic = float(np.mean(np.std(probs_arr, axis=0)))

        # 95% confidence interval on top class probability
        std_err = math.sqrt(pred_var)
        ci_low = max(0.0, mean_p - 1.96 * std_err)
        ci_high = min(1.0, mean_p + 1.96 * std_err)

        is_unc = (epistemic > 0.15 or mean_p < 0.50 or entropy > 1.2)
        if mean_p >= 0.80 and epistemic < 0.08:
            status = "HIGH_CONFIDENCE"
        elif mean_p >= 0.55 and epistemic < 0.15:
            status = "MODERATE_CONFIDENCE"
        elif mean_p >= 0.40:
            status = "LOW_CONFIDENCE"
        else:
            status = "INSUFFICIENT_EVIDENCE"

        model.eval()  # Reset back to eval

        return UncertaintyEstimate(
            mean_prediction=top_class,
            mean_probability=mean_p,
            predictive_variance=pred_var,
            predictive_entropy=entropy,
            epistemic_uncertainty=epistemic,
            confidence_interval_95=(ci_low, ci_high),
            mc_samples_count=self.n_passes,
            is_uncertain=is_unc,
            status_label=status
        )
