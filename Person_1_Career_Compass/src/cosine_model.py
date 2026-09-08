"""Step 6: cosine-similarity recommender.

Ranks every occupation by the cosine similarity between the user's combined,
weighted feature vector and each occupation's combined, weighted feature vector
(built by `vector_builder`, which handles block-width and labor-market target
corrections). Parallel structure to `baseline_model.recommend_baseline` so all
recommenders share the same call shape.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .compatibility import compute_component_scores, normalize_weights
from .feature_matrix import FeatureMatrices
from .scaling import ScaledMatrices
from .user_profile import UserProfile
from .vector_builder import build_occupation_matrix, build_user_vector


def recommend_cosine(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profile: UserProfile,
    weights: dict[str, float] | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    profile.validate()
    w = normalize_weights(weights)

    occupation_matrix = build_occupation_matrix(matrices, scaled, profile, w)
    user_vector = build_user_vector(profile, w)

    sims = cosine_similarity(user_vector.reshape(1, -1), occupation_matrix.to_numpy()).ravel()
    scores = pd.Series(sims, index=occupation_matrix.index, name="cosine_similarity")

    components = compute_component_scores(profile, scaled)
    result = matrices.lookup.join(scores).join(components)
    result["profile_name"] = profile.profile_name
    for name, value in w.items():
        result[f"weight_{name}"] = value

    result = result.sort_values("cosine_similarity", ascending=False).head(top_n).copy()
    result.insert(1, "rank", np.arange(1, len(result) + 1))
    result["model"] = "cosine"
    return result.reset_index(drop=True)