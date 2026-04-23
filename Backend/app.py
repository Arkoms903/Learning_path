from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
import joblib
import pickle
from sklearn.metrics.pairwise import cosine_similarity

from services.recommender import (
    hybrid_recommend,
    get_completed_topics,
    prerequisites_met_for_user,
    cold_start_recommend,
)
from schemas import (
    RecommendRequest,
    NewUserRecommendRequest,
    RecommendResponse,
    TopicRecommendation,
    CompletedTopicsResponse,
    HealthResponse,
)

# ── Global State ──────────────────────────────────────────────────────────────

app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load both pkl files once at startup.

    learning_path_model.pkl  → vectorizer, topic_vectors, topics_df, prerequisites
    interactions.pkl         → interactions_df  (or interactions_encoded.csv as fallback)
    """
    print("Loading model and data from pkl files...")

    # ── Load model bundle (learning_path_model.pkl) ──
    model = joblib.load("data/learning_path_model.pkl")
    app_state["vectorizer"]     = model["Vectorizer"]
    app_state["topic_vectors"]  = model["topic_vectors"]
    app_state["topics_df"]      = model["topics_df"]
    app_state["prerequisites_df"] = model["prerequisites"]

    # ── Load interactions (interactions.pkl or CSV fallback) ──
    try:
        with open("data/interactions.pkl", "rb") as f:
            app_state["interactions_df"] = pickle.load(f)
        print("  Loaded interactions from interactions.pkl")
    except FileNotFoundError:
        app_state["interactions_df"] = pd.read_csv("data/interactions_encoded.csv")
        print("  Loaded interactions from CSV fallback")

    print("✅ Ready!")
    print(f"   Topics: {len(app_state['topics_df'])} | "
          f"Interactions: {len(app_state['interactions_df'])} | "
          f"Prerequisites: {len(app_state['prerequisites_df'])}")
    yield
    app_state.clear()
    print("App shut down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    lifespan=lifespan,
    title="Learning Path Recommender API",
    description="Hybrid ML-based learning path recommendations loaded from pkl files.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ────────────────────────────────────────────────────────────────────

DIFFICULTY_MAP = {0.0: "Beginner", 1.0: "Intermediate", 2.0: "Advanced"}


def build_recs(result_df: pd.DataFrame) -> list[TopicRecommendation]:
    recs = []
    for _, row in result_df.iterrows():
        recs.append(TopicRecommendation(
            topic_id=str(row["topic_id"]),
            topic_name=str(row["topic_name"]),
            difficulty=str(row.get("difficulty", DIFFICULTY_MAP.get(float(row.get("difficulty_encoded", 0)), "Unknown"))),
            estimated_hours=str(row.get("estimated_hours", "")),
            score=float(row["score"]) if "score" in row and pd.notna(row.get("score")) else None,
        ))
    return recs


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse, tags=["Health"])
def root():
    return HealthResponse(status="ok", message="Learning Path Recommender API is running")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    return HealthResponse(status="ok", message="Learning Path Recommender API is running")


# ── Existing Users ──

@app.post("/recommend", response_model=RecommendResponse, tags=["Existing Users"])
def recommend(request: RecommendRequest):
    """Recommendations for an existing user (must be in interactions data)."""
    interactions_df  = app_state["interactions_df"]
    topics_df        = app_state["topics_df"]
    prerequisites_df = app_state["prerequisites_df"]
    topic_vectors    = app_state["topic_vectors"]

    if request.user_id not in interactions_df["user_id"].values:
        raise HTTPException(
            status_code=404,
            detail=f"User '{request.user_id}' not found. Use /recommend/new-user for new users."
        )

    completed     = get_completed_topics(request.user_id, interactions_df)
    is_cold_start = len(completed) == 0

    result_df = hybrid_recommend(
        user_id=request.user_id,
        interactions_df=interactions_df,
        prerequisites_df=prerequisites_df,
        topics_df=topics_df,
        topic_vectors=topic_vectors,
        top_k=request.top_k,
    )

    if result_df.empty:
        raise HTTPException(status_code=404, detail=f"No recommendations found for '{request.user_id}'.")

    return RecommendResponse(
        user_id=request.user_id,
        total=len(result_df),
        is_cold_start=is_cold_start,
        is_new_user=False,
        recommendations=build_recs(result_df),
    )


@app.get("/recommend/{user_id}", response_model=RecommendResponse, tags=["Existing Users"])
def recommend_by_id(user_id: str, top_k: int = Query(default=5, ge=1, le=20)):
    """GET version — easy browser/curl testing. Example: /recommend/U050?top_k=5"""
    return recommend(RecommendRequest(user_id=user_id, top_k=top_k))


@app.get("/user/{user_id}/completed", response_model=CompletedTopicsResponse, tags=["Existing Users"])
def get_user_completed(user_id: str):
    """Returns all topics an existing user has completed."""
    interactions_df = app_state["interactions_df"]
    if user_id not in interactions_df["user_id"].values:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    completed = get_completed_topics(user_id, interactions_df)
    return CompletedTopicsResponse(
        user_id=user_id,
        total_completed=len(completed),
        completed_topic_ids=sorted(list(completed)),
    )


# ── New Users ──

@app.post("/recommend/new-user", response_model=RecommendResponse, tags=["New Users"])
def recommend_new_user(request: NewUserRecommendRequest):
    """
    Recommendations for a new user not in the system.
    Provide a list of topic IDs they have already completed.
    """
    topics_df        = app_state["topics_df"]
    prerequisites_df = app_state["prerequisites_df"]
    topic_vectors    = app_state["topic_vectors"]

    # Validate topic IDs
    valid_ids = set(topics_df["topic_id"].values)
    invalid   = [t for t in request.completed_topic_ids if t not in valid_ids]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown topic IDs: {invalid}. Check /topics.")

    completed = set(request.completed_topic_ids)

    # Build user vector from completed topics
    indices  = topics_df[topics_df["topic_id"].isin(completed)].index
    user_vec = np.asarray(topic_vectors[indices].mean(axis=0))
    sims     = cosine_similarity(user_vec, topic_vectors).flatten()

    topics_scored         = topics_df.copy()
    topics_scored["score"] = sims
    topics_scored         = topics_scored.sort_values("score", ascending=False)

    # Temporary interactions table so prerequisite logic works unchanged
    temp_interactions = pd.DataFrame({
        "user_id":            [request.user_id] * len(completed),
        "topic_id":           list(completed),
        "time_spent":         [0.0] * len(completed),
        "rating":             [0]   * len(completed),
        "completion_encoded": [3.0] * len(completed),
    })

    final = []
    for _, row in topics_scored.iterrows():
        topic_id = row["topic_id"]
        if topic_id in completed:
            continue
        if prerequisites_met_for_user(request.user_id, topic_id, temp_interactions, prerequisites_df):
            row = row.copy()
            row["difficulty"] = DIFFICULTY_MAP.get(float(row["difficulty_encoded"]), "Unknown")
            final.append(row)
        if len(final) == request.top_k:
            break

    if not final:
        raise HTTPException(status_code=404, detail="No recommendations found. Try adding more completed topics.")

    result_df = pd.DataFrame(final)
    return RecommendResponse(
        user_id=request.user_id,
        total=len(result_df),
        is_cold_start=False,
        is_new_user=True,
        recommendations=build_recs(result_df),
    )


@app.get("/recommend/cold-start", response_model=RecommendResponse, tags=["New Users"])
def recommend_cold_start(top_k: int = Query(default=5, ge=1, le=20)):
    """Beginner topics for absolute beginners with no prior knowledge."""
    topics_df = app_state["topics_df"]
    result_df = cold_start_recommend(topics_df, top_k=top_k).copy()
    result_df["difficulty"] = result_df["difficulty_encoded"].map(DIFFICULTY_MAP)
    return RecommendResponse(
        user_id="anonymous",
        total=len(result_df),
        is_cold_start=True,
        is_new_user=True,
        recommendations=build_recs(result_df),
    )


# ── Topics ──

@app.get("/topics", tags=["Topics"])
def list_topics():
    """All available topics — useful for new users to find topic IDs."""
    topics_df = app_state["topics_df"]
    topics = []
    for _, row in topics_df.iterrows():
        topics.append({
            "topic_id":        row["topic_id"],
            "topic_name":      row["topic_name"],
            "difficulty":      DIFFICULTY_MAP.get(float(row["difficulty_encoded"]), "Unknown"),
            "estimated_hours": row["estimated_hours"],
        })
    return {"total": len(topics), "topics": topics}