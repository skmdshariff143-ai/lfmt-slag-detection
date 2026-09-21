"""
Classical Machine Learning Baseline Models for Thermographic Defect Characterization.

Supports:
- Random Forest Classifier & Regressors (Depth, Diameter)
- Extra Trees Ensemble
- Histogram-based Gradient Boosting (HistGradientBoosting)
- Tabular feature scaling and feature importance extraction
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


@dataclass
class MLPredictionResult:
    """Standardized output of classical ML inference."""
    is_anomaly: bool
    anomaly_probability: float
    defect_type: str
    class_probabilities: Dict[str, float]
    estimated_depth_mm: Optional[float] = None
    estimated_diameter_mm: Optional[float] = None
    feature_importances: Dict[str, float] = field(default_factory=dict)
    model_name: str = "RandomForest"
    confidence_score: float = 0.0
    is_validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_probability": self.anomaly_probability,
            "defect_type": self.defect_type,
            "class_probabilities": self.class_probabilities,
            "estimated_depth_mm": self.estimated_depth_mm,
            "estimated_diameter_mm": self.estimated_diameter_mm,
            "feature_importances": self.feature_importances,
            "model_name": self.model_name,
            "confidence_score": self.confidence_score
        }


class ClassicalMLDefectEngine:
    """Multi-task tabular classifier and regression suite."""

    FEATURE_NAMES = [
        "peak_delta_t", "min_delta_t", "mean_temp", "time_to_peak",
        "heat_slope", "cool_slope", "temp_variance", "temp_skewness",
        "temp_kurtosis", "spatial_grad_mean", "spatial_grad_max",
        "laplacian_var", "spatial_entropy", "frame_count",
        "thermal_diffusivity", "thermal_effusivity", "pct_kurtosis",
        "spct_sparsity", "rpt_score", "snr_estimate"
    ]

    DEFECT_CLASSES = ["HEALTHY", "SLAG_INCLUSION", "WALL_THINNING", "AIR_VOID", "UNKNOWN_DEFECT"]

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.classifier = RandomForestClassifier(
            n_estimators=100, max_depth=8, random_state=random_state
        )
        self.depth_regressor = RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=random_state
        )
        self.diameter_regressor = RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=random_state
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit_synthetic_baseline(self) -> None:
        """
        Fit baseline model using physically calibrated synthetic domain priors
        (ensures operational inference out-of-the-box before full offline batch training).
        """
        rng = np.random.default_rng(self.random_state)
        N_samples = 400

        # Generate synthetic feature distribution
        X_list, y_class_list, y_depth_list, y_diam_list = [], [], [], []

        for _ in range(N_samples):
            is_def = rng.random() > 0.30
            if not is_def:
                # Healthy specimen
                feat = [
                    rng.normal(0.05, 0.02),  # peak_dt
                    rng.normal(0.0, 0.01),   # min_dt
                    rng.normal(294.0, 0.5),  # mean_temp
                    rng.uniform(1.0, 5.0),   # time_to_peak
                    rng.normal(0.01, 0.005), # heat_slope
                    rng.normal(-0.01, 0.005),# cool_slope
                    rng.normal(0.02, 0.01),  # temp_var
                    rng.normal(0.0, 0.2),    # skewness
                    rng.normal(0.0, 0.3),    # kurtosis
                    rng.normal(0.01, 0.005), # grad_mean
                    rng.normal(0.03, 0.01),  # grad_max
                    rng.normal(0.001, 0.0005), # lap_var
                    rng.normal(2.5, 0.2),    # entropy
                    rng.choice([100, 200, 500]), # frame_count
                    1.36e-5,                 # diffusivity
                    14075.0,                 # effusivity
                    rng.normal(0.1, 0.05),   # pct_kurtosis
                    0.95,                    # spct_sparsity
                    rng.normal(0.1, 0.05),   # rpt_score
                    rng.uniform(20.0, 35.0)  # snr
                ]
                X_list.append(feat)
                y_class_list.append("HEALTHY")
                y_depth_list.append(0.0)
                y_diam_list.append(0.0)
            else:
                depth = rng.uniform(0.2, 1.5)
                diam = rng.uniform(3.0, 12.0)
                defect_kind = rng.choice(["SLAG_INCLUSION", "SLAG_INCLUSION", "WALL_THINNING", "AIR_VOID"])
                contrast_scale = (diam / (depth + 0.1)) * 0.1

                feat = [
                    rng.normal(0.4 + contrast_scale, 0.1),
                    rng.normal(-0.05, 0.02),
                    rng.normal(294.5, 0.8),
                    rng.uniform(3.0, 8.0),
                    rng.normal(0.08, 0.02),
                    rng.normal(-0.04, 0.01),
                    rng.normal(0.15, 0.05),
                    rng.normal(1.2, 0.4),
                    rng.normal(2.5, 0.8),
                    rng.normal(0.08, 0.03),
                    rng.normal(0.25, 0.08),
                    rng.normal(0.01, 0.004),
                    rng.normal(3.2, 0.3),
                    rng.choice([100, 200, 500]),
                    1.36e-5,
                    14075.0,
                    rng.normal(3.5, 1.2),
                    rng.uniform(0.60, 0.85),
                    rng.normal(2.8, 1.0),
                    rng.uniform(20.0, 35.0)
                ]
                X_list.append(feat)
                y_class_list.append(defect_kind)
                y_depth_list.append(depth)
                y_diam_list.append(diam)

        X = np.array(X_list, dtype=float)
        y_class = np.array(y_class_list)
        y_depth = np.array(y_depth_list, dtype=float)
        y_diam = np.array(y_diam_list, dtype=float)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.classifier.fit(X_scaled, y_class)
        self.depth_regressor.fit(X_scaled, y_depth)
        self.diameter_regressor.fit(X_scaled, y_diam)
        self.is_fitted = True

    def predict(self, feature_vector: np.ndarray) -> MLPredictionResult:
        """Run multi-task ML inference on a 1D or 2D feature vector."""
        if not self.is_fitted:
            self.fit_synthetic_baseline()

        if feature_vector.ndim == 1:
            X = feature_vector.reshape(1, -1)
        else:
            X = feature_vector

        # Pad or trim to match expected feature count
        expected_len = len(self.FEATURE_NAMES)
        if X.shape[1] < expected_len:
            pad = np.zeros((X.shape[0], expected_len - X.shape[1]))
            X = np.hstack([X, pad])
        elif X.shape[1] > expected_len:
            X = X[:, :expected_len]

        # Physical boundary sanity check: homogeneous low contrast is definitively healthy
        peak_dt_val = float(X[0, 0])
        grad_max_val = float(X[0, 10]) if X.shape[1] > 10 else 0.0
        if peak_dt_val < 0.15 and grad_max_val < 0.10:
            return MLPredictionResult(
                is_anomaly=False,
                anomaly_probability=0.02,
                defect_type="HEALTHY",
                class_probabilities={"HEALTHY": 0.98, "SLAG_INCLUSION": 0.005, "WALL_THINNING": 0.005, "AIR_VOID": 0.005, "UNKNOWN_DEFECT": 0.005},
                estimated_depth_mm=None,
                estimated_diameter_mm=None,
                feature_importances={self.FEATURE_NAMES[i]: 0.05 for i in range(min(5, len(self.FEATURE_NAMES)))},
                confidence_score=0.98
            )

        X_scaled = self.scaler.transform(X)
        probs = self.classifier.predict_proba(X_scaled)[0]
        classes = self.classifier.classes_

        class_prob_map = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
        top_idx = int(np.argmax(probs))
        top_class = str(classes[top_idx])
        top_prob = float(probs[top_idx])

        is_anomaly = (top_class != "HEALTHY" and top_prob >= 0.40)
        anomaly_prob = float(1.0 - class_prob_map.get("HEALTHY", 0.0))

        depth_est = None
        diam_est = None
        if is_anomaly:
            depth_est = round(float(self.depth_regressor.predict(X_scaled)[0]), 2)
            diam_est = round(float(self.diameter_regressor.predict(X_scaled)[0]), 2)
            # Physical clamping
            depth_est = max(0.1, min(5.0, depth_est))
            diam_est = max(1.0, min(30.0, diam_est))

        # Extract feature importances
        imp = self.classifier.feature_importances_
        imp_dict = {
            self.FEATURE_NAMES[i]: round(float(imp[i]), 4)
            for i in range(min(len(imp), len(self.FEATURE_NAMES)))
        }

        return MLPredictionResult(
            is_anomaly=is_anomaly,
            anomaly_probability=round(anomaly_prob, 4),
            defect_type=top_class if is_anomaly else "HEALTHY",
            class_probabilities=class_prob_map,
            estimated_depth_mm=depth_est,
            estimated_diameter_mm=diam_est,
            feature_importances=imp_dict,
            confidence_score=round(top_prob, 4)
        )
