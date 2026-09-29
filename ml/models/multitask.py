"""
Physics-Informed Multi-Task Neural Network for Thermographic NDT.

Integrates:
- Spatial-temporal thermal representation learning
- Physics metadata injection (f0, f1, q0, thermal diffusivity, effusivity, duration)
- Multi-task heads:
    * Head A: Healthy / Defect Multi-Class Probability
    * Head B: High-Resolution Defect Segmentation Map
    * Head C: Defect Depth Regression (mm)
    * Head D: Defect Equivalent Diameter Regression (mm)
    * Head E: Centroid Coordinates (x_mm, y_mm)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.models.deep_learning import UNetLite


@dataclass
class MultiTaskPrediction:
    """Output container for Physics-Informed Multi-Task Network."""
    defect_type: str
    class_probabilities: Dict[str, float]
    anomaly_probability: float
    segmentation_mask: np.ndarray        # (H, W) float in [0, 1]
    binary_mask: np.ndarray              # (H, W) bool
    estimated_depth_mm: Optional[float]
    estimated_diameter_mm: Optional[float]
    predicted_centroid_mm: Optional[Tuple[float, float]]
    confidence_score: float
    latent_embedding: np.ndarray
    is_validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "defect_type": self.defect_type,
            "class_probabilities": self.class_probabilities,
            "anomaly_probability": round(self.anomaly_probability, 4),
            "estimated_depth_mm": self.estimated_depth_mm,
            "estimated_diameter_mm": self.estimated_diameter_mm,
            "predicted_centroid_mm": list(self.predicted_centroid_mm) if self.predicted_centroid_mm else None,
            "confidence_score": round(self.confidence_score, 4),
            "segmentation_active": bool(np.any(self.binary_mask))
        }


class PhysicsInformedMultiTaskNet(nn.Module):
    """
    Shared Encoder with Physics Metadata Fusion & Multi-Task Heads.
    """

    CLASS_NAMES = ["HEALTHY", "SLAG_INCLUSION", "WALL_THINNING", "AIR_VOID", "UNKNOWN_DEFECT"]

    def __init__(
        self,
        in_channels: int = 1,
        num_classes: int = 5,
        physics_dim: int = 8
    ):
        super().__init__()
        self.num_classes = num_classes
        self.physics_dim = physics_dim

        # 1. Spatial Encoder Backbone
        self.encoder_conv = nn.Sequential(
            nn.Conv2d(in_channels, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4))
        )

        # 2. Physics Metadata Injection Layer
        self.physics_mlp = nn.Sequential(
            nn.Linear(physics_dim, 16),
            nn.ReLU(inplace=True),
            nn.Linear(16, 16)
        )

        # 3. Fused Latent Representation
        # 64 * 4 * 4 = 1024 + 16 physics = 1040
        self.latent_dim = 1024 + 16
        self.shared_dense = nn.Sequential(
            nn.Linear(self.latent_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25)
        )

        # 4. Multi-Task Heads
        self.head_class = nn.Linear(128, num_classes)
        self.head_depth = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1)
        )
        self.head_diam = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 1)
        )
        self.head_centroid = nn.Sequential(
            nn.Linear(128, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 2)
        )

        # 5. Segmentation Decoder (U-Net Lite branch)
        self.seg_decoder = UNetLite(in_channels=in_channels, out_channels=1)

    def forward(
        self,
        x_image: torch.Tensor,
        x_physics: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        Args:
            x_image: (B, C, H, W) thermal map tensor.
            x_physics: (B, physics_dim) thermodynamic parameters.
        """
        B = x_image.shape[0]
        if x_physics is None:
            x_physics = torch.zeros((B, self.physics_dim), device=x_image.device)

        # Spatial encoding
        img_feats = self.encoder_conv(x_image).flatten(1)  # (B, 1024)
        phys_feats = self.physics_mlp(x_physics)            # (B, 16)

        fused = torch.cat([img_feats, phys_feats], dim=1)   # (B, 1040)
        latent = self.shared_dense(fused)                   # (B, 128)

        # Task Heads
        logits = self.head_class(latent)
        depth = F.relu(self.head_depth(latent))
        diam = F.relu(self.head_diam(latent))
        centroid = self.head_centroid(latent)

        # Segmentation
        seg_mask = self.seg_decoder(x_image)

        return logits, seg_mask, depth, diam, centroid, latent


class MultiTaskInferenceEngine:
    """Inference runner for PhysicsInformedMultiTaskNet."""

    def __init__(self, in_channels: int = 1):
        torch.manual_seed(42)
        self.model = PhysicsInformedMultiTaskNet(in_channels=in_channels)
        self.model.eval()

    def predict(
        self,
        map_image: np.ndarray,
        physics_vec: Optional[np.ndarray] = None,
        threshold: float = 0.50
    ) -> MultiTaskPrediction:
        """Run single-sample inference."""
        if map_image.ndim == 2:
            map_image = map_image[np.newaxis, np.newaxis, :, :]
        elif map_image.ndim == 3:
            map_image = map_image[np.newaxis, :, :, :]

        H, W = map_image.shape[2], map_image.shape[3]
        img_tensor = torch.from_numpy(map_image).float()

        if physics_vec is None:
            phys_tensor = torch.zeros((1, 8)).float()
        else:
            phys_tensor = torch.from_numpy(physics_vec).float().view(1, -1)
            if phys_tensor.shape[1] < 8:
                phys_tensor = F.pad(phys_tensor, (0, 8 - phys_tensor.shape[1]))
            elif phys_tensor.shape[1] > 8:
                phys_tensor = phys_tensor[:, :8]

        # Physical check for truly flat uniform map
        map_std = float(np.std(map_image))
        map_ptp = float(np.ptp(map_image))
        if map_ptp < 1e-4 or map_std < 1e-5:
            classes = PhysicsInformedMultiTaskNet.CLASS_NAMES
            prob_dict = {c: (0.96 if c == "HEALTHY" else 0.01) for c in classes}
            return MultiTaskPrediction(
                defect_type="HEALTHY",
                class_probabilities=prob_dict,
                anomaly_probability=0.04,
                segmentation_mask=np.zeros((H, W), dtype=float),
                binary_mask=np.zeros((H, W), dtype=bool),
                estimated_depth_mm=None,
                estimated_diameter_mm=None,
                predicted_centroid_mm=None,
                confidence_score=0.96,
                latent_embedding=np.zeros(128, dtype=float)
            )

        with torch.no_grad():
            logits, seg_mask, depth, diam, centroid, latent = self.model(img_tensor, phys_tensor)

        probs = F.softmax(logits, dim=1).numpy()[0]
        classes = PhysicsInformedMultiTaskNet.CLASS_NAMES
        prob_dict = {classes[i]: round(float(probs[i]), 4) for i in range(len(classes))}

        top_idx = int(np.argmax(probs))
        top_class = classes[top_idx]
        anomaly_prob = float(1.0 - prob_dict.get("HEALTHY", 0.0))

        is_anomaly = (top_class != "HEALTHY" and anomaly_prob >= 0.35)
        seg_np = seg_mask.squeeze().numpy()
        bin_mask = (seg_np >= threshold)

        d_val = round(float(depth.numpy()[0, 0]), 2) if is_anomaly else None
        diam_val = round(float(diam.numpy()[0, 0]), 2) if is_anomaly else None
        c_val = (round(float(centroid.numpy()[0, 0]), 2), round(float(centroid.numpy()[0, 1]), 2)) if is_anomaly else None

        return MultiTaskPrediction(
            defect_type=top_class if is_anomaly else "HEALTHY",
            class_probabilities=prob_dict,
            anomaly_probability=round(anomaly_prob, 4),
            segmentation_mask=seg_np,
            binary_mask=bin_mask,
            estimated_depth_mm=d_val,
            estimated_diameter_mm=diam_val,
            predicted_centroid_mm=c_val,
            confidence_score=round(float(probs[top_idx]), 4),
            latent_embedding=latent.numpy()[0]
        )
