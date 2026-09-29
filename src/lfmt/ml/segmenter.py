"""Small NumPy segmentation network: temporal channels + fixed spatial pooling.

Equivalent to two learned 1x1 convolution layers on temporal feature images.
No coordinates or ground-truth inputs are used at inference.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def features(cube: FloatArray) -> FloatArray:
    if cube.ndim != 3 or cube.shape[0] < 8 or not np.isfinite(cube).all():
        raise ValueError("Expected at least eight finite thermogram frames")
    indices = np.linspace(0, cube.shape[0] - 1, 8).astype(int)
    channels = cube[indices] - cube[0]
    channels -= np.median(channels, axis=(1, 2), keepdims=True)
    pad = np.pad(channels, ((0, 0), (1, 1), (1, 1)), mode="reflect")
    pooled = (
        pad[:, :-2, :-2]
        + pad[:, :-2, 1:-1]
        + pad[:, :-2, 2:]
        + pad[:, 1:-1, :-2]
        + pad[:, 1:-1, 1:-1]
        + pad[:, 1:-1, 2:]
        + pad[:, 2:, :-2]
        + pad[:, 2:, 1:-1]
        + pad[:, 2:, 2:]
    ) / 9.0
    res = np.concatenate([channels, pooled], axis=0).reshape(16, -1).T
    return cast(FloatArray, np.asarray(res, dtype=np.float64))


class TemporalPixelSegmenter:
    def __init__(self, seed: int = 2026) -> None:
        rng = np.random.default_rng(seed)
        self.w1 = rng.normal(0, .1, (16, 16))
        self.b1 = np.zeros(16)
        self.w2 = rng.normal(0, .1, 16)
        self.b2 = np.zeros(1)
        self.mean = np.zeros(16)
        self.scale = np.ones(16)
        self.trained = False

    def fit(self, x: FloatArray, y: FloatArray, epochs: int = 600, learning_rate: float = .03) -> list[float]:
        if x.ndim != 2 or x.shape[1] != 16 or y.shape != (x.shape[0],):
            raise ValueError("Training features and labels have incompatible shapes")
        if not np.isfinite(x).all() or not np.isin(y, [0, 1]).all() or np.unique(y).size != 2:
            raise ValueError("Finite features and both binary classes are required")
        self.mean = x.mean(axis=0)
        self.scale = np.maximum(x.std(axis=0), 1e-6)
        x = np.clip((x - self.mean) / self.scale, -10, 10)
        sample_weight = np.where(y == 1, .5 / y.sum(), .5 / (1 - y).sum())
        losses = []
        for _ in range(epochs):
            hidden = np.tanh(x @ self.w1 + self.b1)
            logits = hidden @ self.w2 + self.b2[0]
            probability = 1 / (1 + np.exp(-np.clip(logits, -40, 40)))
            losses.append(float(np.sum(sample_weight * (np.logaddexp(0, logits) - y * logits))))
            delta = (probability - y) * sample_weight
            hidden_delta = delta[:, None] * self.w2 * (1 - hidden ** 2)
            self.w2 -= learning_rate * (hidden.T @ delta)
            self.b2 -= learning_rate * delta.sum()
            self.w1 -= learning_rate * (x.T @ hidden_delta)
            self.b1 -= learning_rate * hidden_delta.sum(axis=0)
        self.trained = True
        return losses

    def predict(self, cube: FloatArray) -> FloatArray:
        if not self.trained:
            raise ValueError("Train or load the segmentation baseline before inference")
        x = np.clip((features(cube) - self.mean) / self.scale, -10, 10)
        logits = np.tanh(x @ self.w1 + self.b1) @ self.w2 + self.b2[0]
        prob = 1.0 / (1.0 + np.exp(-np.clip(logits, -40.0, 40.0)))
        return cast(FloatArray, np.asarray(prob.reshape(cube.shape[1:]), dtype=np.float64))

    def save(self, path: Path) -> None:
        if not self.trained:
            raise ValueError("Cannot save an untrained model")
        payload = {name: getattr(self, name).tolist() for name in ["w1", "b1", "w2", "b2", "mean", "scale"]}
        payload["version"] = "temporal-pixel-v1"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> TemporalPixelSegmenter:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != "temporal-pixel-v1":
            raise ValueError("Unsupported segmentation model version")
        model = cls()
        for name in ["w1", "b1", "w2", "b2", "mean", "scale"]:
            value = np.asarray(data[name], dtype=np.float64)
            if value.shape != getattr(model, name).shape or not np.isfinite(value).all():
                raise ValueError(f"Invalid model parameter: {name}")
            setattr(model, name, value)
        if np.any(model.scale <= 0):
            raise ValueError("Invalid feature scale")
        model.trained = True
        return model
