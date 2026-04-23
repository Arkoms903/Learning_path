import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# ── User History ──────────────────────────────────────────────────────────────

def get_completed_topics(user_id, interactions_df):
    """Returns set of topic_ids the user has completed (completion_encoded == 3)."""
    return set(
        interactions_df[
            (interactions_df["user_id"] == user_id) &
            (interactions_df["completion_encoded"] == 3.0)
        ]["topic_id"]
    )


def prerequisites_met_for_user(user_id, topic_id, interactions_df, prerequisites_df):
    """Returns True if all prerequisites of the topic are completed by the user."""
    completed = get_completed_topics(user_id, interactions_df)
    prereqs = prerequisites_df[
        prerequisites_df["topic_id"] == topic_id
    ]["prerequisite_id"].tolist()
    return all(pr in completed for pr in prereqs)


# ── User Profile ──────────────────────────────────────────────────────────────

def get_user_profile(user_id, interactions_df, topics_df, topic_vectors):
    """Builds a TF-IDF average vector from the user's completed topics."""
    completed = get_completed_topics(user_id, interactions_df)
    indices = topics_df[topics_df["topic_id"].isin(completed)].index
    if len(indices) == 0:
        return np.zeros((1, topic_vectors.shape[1]))
    return topic_vectors[indices].mean(axis=0)


# ── Difficulty Progression ────────────────────────────────────────────────────

def get_user_level(user_id, interactions_df, topics_df):
    """Returns the user's current difficulty level (0=Beginner, 1=Intermediate, 2=Advanced)."""
    completed = get_completed_topics(user_id, interactions_df)
    if not completed:
        return 0.0
    levels = topics_df[
        topics_df["topic_id"].isin(completed)
    ]["difficulty_encoded"].astype(float).tolist()
    return max(levels) if levels else 0.0


def difficulty_boost(topic_difficulty, user_level):
    """
    Multiplier to push users toward topics at or one step above their level.
    topic_difficulty and user_level are floats: 0.0, 1.0, 2.0
    """
    diff = topic_difficulty - user_level
    if diff > 0:
        return 1.3    # Topic harder than user → encourage progression
    elif diff == 0:
        return 1.0    # Same level → neutral
    elif diff == -1:
        return 0.4    # One level below → mild penalty
    else:
        return 0.2    # Two levels below → strong penalty


# ── ML Recommendation Engine ──────────────────────────────────────────────────

def ml_recommend_topics(user_id, interactions_df, topics_df, topic_vectors, top_k=50):
    """TF-IDF cosine similarity + difficulty progression boost."""
    user_vec = np.asarray(get_user_profile(user_id, interactions_df, topics_df, topic_vectors))
    sims = cosine_similarity(user_vec, topic_vectors).flatten()

    user_level = get_user_level(user_id, interactions_df, topics_df)

    topics_scored = topics_df.copy()
    topics_scored["similarity"] = sims
    topics_scored["difficulty_boost"] = topics_scored["difficulty_encoded"].astype(float).apply(
        lambda d: difficulty_boost(d, user_level)
    )
    topics_scored["score"] = topics_scored["similarity"] * topics_scored["difficulty_boost"]

    return topics_scored.sort_values("score", ascending=False).head(top_k)


# ── Cold Start ────────────────────────────────────────────────────────────────

def cold_start_recommend(topics_df, top_k=5):
    """For new users with no history: return top beginner topics."""
    return topics_df[topics_df["difficulty_encoded"] == 0].head(top_k)


# ── Hybrid Recommender ────────────────────────────────────────────────────────

def hybrid_recommend(user_id, interactions_df, prerequisites_df, topics_df, topic_vectors, top_k=5):
    """
    Main recommendation function:
    - No history  → cold start (beginner topics)
    - Has history → ML scoring + prerequisite filtering + exclude completed
    """
    completed = get_completed_topics(user_id, interactions_df)

    if len(completed) == 0:
        return cold_start_recommend(topics_df, top_k=top_k)

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