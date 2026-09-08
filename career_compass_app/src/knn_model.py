"""Step 7: K-nearest-neighbors recommender.

No label being predicted, only a nearest-neighbor search over the same weighted feature
space `vector_builder` builds for the cosine model. `metric` selects which distance
function defines "nearest": euclidean and manhattan are sensitive to absolute position
in the scaled feature space, minkowski generalizes both via its `p`
exponent, and cosine ignores magnitude entirely and ranks on direction only. Each
metric can surface a different top-N even from identical input vectors. 
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from .compatibility import compute_component_scores, normalize_weights
from .feature_matrix import FeatureMatrices
from .scaling import ScaledMatrices
from .user_profile import UserProfile
from .vector_builder import build_occupation_matrix, build_user_vector

# Distance metrics evaluated for the KNN recommenders
# Minkowski defaults to p=3 so it's a distinct generalization than euclidean (p=2) or manhattan (p=1).

KNN_METRICS: dict[str, dict[str, float]] = {
    "euclidean": {},
    "manhattan": {},
    "minkowski": {"p": 3},
    "cosine": {},
}


def recommend_knn(
    matrices: FeatureMatrices,
    scaled: ScaledMatrices,
    profile: UserProfile,
    weights: dict[str, float] | None = None,
    k: int = 10,
    metric: str = "euclidean",
    **metric_kwargs,
) -> pd.DataFrame:
    profile.validate()
    w = normalize_weights(weights)

    occupation_matrix = build_occupation_matrix(matrices, scaled, profile, w)
    user_vector = build_user_vector(profile, w)

    k = min(k, len(occupation_matrix))
    model = NearestNeighbors(n_neighbors=k, metric=metric, **metric_kwargs)
    model.fit(occupation_matrix.to_numpy())
    distances, indices = model.kneighbors(user_vector.reshape(1, -1))

    neighbor_index = occupation_matrix.index[indices[0]]
    distance_column = f"{metric}_distance"
    
    result_scores = pd.Series(1.0 / (1.0 + distances[0]), index=neighbor_index, name="knn_similarity")
    result_distance = pd.Series(distances[0], index=neighbor_index, name=distance_column)

    components = compute_component_scores(profile, scaled).loc[neighbor_index]
    result = matrices.lookup.loc[neighbor_index].join(result_scores).join(result_distance).join(components)
    result["profile_name"] = profile.profile_name
    for name, value in w.items():
        result[f"weight_{name}"] = value

    result = result.sort_values(distance_column, ascending=True).copy()
    result.insert(1, "rank", np.arange(1, len(result) + 1))
    result["model"] = f"knn_{metric}"
    result["distance_metric"] = metric
    return result.reset_index(drop=True)