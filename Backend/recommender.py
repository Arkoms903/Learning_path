import numpy as np
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------------------
# Encoding Utilities
# -----------------------------------------

def encode_topics(topics_df):
    """
    Encodes topics DataFrame with difficulty_encoded and domain one-hot columns.
    Returns: (encoded topics_df, fitted ohe encoder, topic_vectors, vectorizer)
    """
    # Ordinal encode difficulty
    difficulty_encoder = OrdinalEncoder(
        categories=[["Beginner", "Intermediate", "Advanced"]]
    )
    topics_df = topics_df.copy()
    topics_df["difficulty_encoded"] = difficulty_encoder.fit_transform(
        topics_df[["difficulty"]]
    )

    # One-hot encode domain
    ohe = OneHotEncoder(drop="first")
    domain_encoded = ohe.fit_transform(topics_df[["domain"]]).toarray()
    domain_cols = ohe.get_feature_names_out(["domain"])

    topics_last = np.hstack(
        (
            topics_df[["topic_id", "topic_name", "estimated_hours", "difficulty_encoded"]].values,
            domain_encoded,
        )
    )

    topics_features = pd.DataFrame(
        topics_last,
        columns=["topic_id", "topic_name", "estimated_hours", "difficulty_encoded"]
        + list(domain_cols),
    )

    # TF-IDF vectorize topic names
    vectorizer = TfidfVectorizer()
    topic_vectors = vectorizer.fit_transform(topics_features["topic_name"])

    return topics_features, ohe, topic_vectors, vectorizer


def encode_interactions(interactions_df):
    """
    Encodes the completion_status column into completion_encoded (0-3).
    Skipped=0, Not Started=1, In Progress=2, Completed=3
    Returns encoded interactions DataFrame (subset of needed columns).
    """
    encoder = OrdinalEncoder(
        categories=[["Skipped", "Not Started", "In Progress", "Completed"]]
    )
    interactions_df = interactions_df.copy()
    interactions_df["completion_encoded"] = encoder.fit_transform(
        interactions_df[["completion_status"]]
    )
    return interactions_df[["user_id", "topic_id", "time_spent", "rating", "completion_encoded"]]


# -----------------------------------------
# User History Utilities
# -----------------------------------------

def get_completed_topics(user_id, interactions_df):
    """
    Returns set of completed topic_ids for a user (completion_encoded == 3.0).
    """
    return set(
        interactions_df[
            (interactions_df["user_id"] == user_id)
            & (interactions_df["completion_encoded"] == 3.0)
        ]["topic_id"]
    )


def prerequisites_met_for_user(user_id, topic_id, interactions_df, prerequisites_df):
    """
    Check if all prerequisites of a topic are completed by user.
    """
    completed_topics = get_completed_topics(user_id, interactions_df)
    prereqs = prerequisites_df[
        prerequisites_df["topic_id"] == topic_id
    ]["prerequisite_id"].tolist()
    return all(pr in completed_topics for pr in prereqs)


# -----------------------------------------
# User Profile (for ML recommendations)
# -----------------------------------------

def get_user_profile(user_id, interactions_df, topics_df, topic_vectors):
    """
    Generate user embedding vector from completed topics using TF-IDF vectors.
    """
    completed = get_completed_topics(user_id, interactions_df)
    indices = topics_df[topics_df["topic_id"].isin(completed)].index

    if len(indices) == 0:
        return np.zeros((1, topic_vectors.shape[1]))

    return topic_vectors[indices].mean(axis=0)


# -----------------------------------------
# ML Recommendation Engine (TF-IDF cosine similarity)
# -----------------------------------------

def get_user_level(user_id, interactions_df, topics_df):
    """
    Determine the user's current difficulty level based on completed topics.

    Logic:
    - If user has completed any Advanced topics     → user level = 2.0 (Advanced)
    - If user has completed any Intermediate topics → user level = 1.0 (Intermediate)
    - Otherwise                                     → user level = 0.0 (Beginner)

    Returns float: 0.0, 1.0, or 2.0
    """
    completed = get_completed_topics(user_id, interactions_df)
    if not completed:
        return 0.0

    completed_difficulties = topics_df[
        topics_df["topic_id"].isin(completed)
    ]["difficulty_encoded"].astype(float).tolist()

    if not completed_difficulties:
        return 0.0

    return max(completed_difficulties)


def difficulty_boost(topic_difficulty, user_level):
    """
    Returns a boost multiplier based on how the topic difficulty
    compares to the user's current level.

    Goal: push users toward topics AT or ONE STEP above their level.
    Penalize topics that are too easy (below user level).

    topic_difficulty and user_level are floats: 0.0, 1.0, 2.0

    Examples:
      user_level=0 (Beginner),     topic=Beginner(0)     → neutral  (1.0)
      user_level=0 (Beginner),     topic=Intermediate(1) → boost    (1.3)
      user_level=1 (Intermediate), topic=Beginner(0)     → penalty  (0.4)
      user_level=1 (Intermediate), topic=Intermediate(1) → neutral  (1.0)
      user_level=1 (Intermediate), topic=Advanced(2)     → boost    (1.3)
      user_level=2 (Advanced),     topic=Beginner(0)     → penalty  (0.2)
      user_level=2 (Advanced),     topic=Intermediate(1) → penalty  (0.5)
      user_level=2 (Advanced),     topic=Advanced(2)     → neutral  (1.0)
    """
    diff = topic_difficulty - user_level

    if diff > 0:
        # Topic is harder than user's current level → encourage progression
        return 1.3
    elif diff == 0:
        # Same level → neutral
        return 1.0
    elif diff == -1:
        # One level below → mild penalty
        return 0.4
    else:
        # Two levels below → strong penalty
        return 0.2


def ml_recommend_topics(user_id, interactions_df, topics_df, topic_vectors, top_k=50):
    """
    Recommend topics using TF-IDF cosine similarity + difficulty progression boost.

    Final score = cosine_similarity * difficulty_boost_multiplier

    This ensures users are pushed toward appropriate next-level topics
    rather than staying at the same difficulty they already completed.
    """
    user_vec = np.asarray(get_user_profile(user_id, interactions_df, topics_df, topic_vectors))
    sims = cosine_similarity(user_vec, topic_vectors).flatten()

    user_level = get_user_level(user_id, interactions_df, topics_df)

    topics_df = topics_df.copy()
    topics_df["similarity"] = sims

    # Apply difficulty boost to each candidate topic
    topics_df["difficulty_boost"] = topics_df["difficulty_encoded"].astype(float).apply(
        lambda d: difficulty_boost(d, user_level)
    )

    # Final score = similarity * boost
    topics_df["score"] = topics_df["similarity"] * topics_df["difficulty_boost"]

    return topics_df.sort_values("score", ascending=False).head(top_k)


# -----------------------------------------
# Cold Start (new user with no history)
# -----------------------------------------

def cold_start_recommend(topics_df, top_k=5):
    """
    For new users with no history: recommend beginner-level topics.
    """
    return topics_df[topics_df["difficulty_encoded"] == 0].head(top_k)


# -----------------------------------------
# Hybrid Recommendation System
# -----------------------------------------

def hybrid_recommend(user_id, interactions_df, prerequisites_df, topics_df, topic_vectors, top_k=5):
    """
    Hybrid recommender with difficulty progression:
    - New user (no history)  → cold start (beginner topics)
    - Existing user          → TF-IDF cosine similarity
                               + difficulty progression boost
                               + prerequisite filtering
                               + exclude already completed topics

    A user who has completed Beginner topics will automatically get
    Intermediate recommendations boosted higher than more Beginner ones.
    """
    completed = get_completed_topics(user_id, interactions_df)

    if len(completed) == 0:
        return cold_start_recommend(topics_df, top_k=top_k)

    # ML candidates with difficulty-aware scoring
    ml_recs = ml_recommend_topics(user_id, interactions_df, topics_df, topic_vectors, top_k=50)

    final = []
    for _, row in ml_recs.iterrows():
        topic_id = row["topic_id"]

        if topic_id in completed:
            continue

        if prerequisites_met_for_user(user_id, topic_id, interactions_df, prerequisites_df):
            final.append(row)

        if len(final) == top_k:
            break

    result_df = pd.DataFrame(final)

    if not result_df.empty and "difficulty_encoded" in result_df.columns:
        difficulty_map = {0.0: "Beginner", 1.0: "Intermediate", 2.0: "Advanced"}
        result_df["difficulty"] = result_df["difficulty_encoded"].map(difficulty_map)

    return result_df