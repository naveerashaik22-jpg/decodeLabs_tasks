import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Movie Recommendation System",
    page_icon="🎬",
    layout="wide"
)

# ============================================================
# MOVIE DATASET
# ============================================================

movies = pd.DataFrame([
    ["Interstellar", "Sci-Fi", "Thoughtful", "English", 8.7],
    ["Inception", "Sci-Fi", "Mysterious", "English", 8.8],
    ["The Martian", "Sci-Fi", "Inspirational", "English", 8.0],
    ["Avatar", "Sci-Fi", "Adventure", "English", 7.8],
    ["Avengers: Endgame", "Action", "Exciting", "English", 8.4],
    ["The Dark Knight", "Action", "Dark", "English", 9.0],
    ["Mad Max: Fury Road", "Action", "Exciting", "English", 8.1],
    ["John Wick", "Action", "Exciting", "English", 7.4],

    ["3 Idiots", "Comedy", "Inspirational", "Hindi", 8.4],
    ["Zindagi Na Milegi Dobara", "Comedy", "Fun", "Hindi", 8.2],
    ["Hera Pheri", "Comedy", "Fun", "Hindi", 8.1],
    ["The Hangover", "Comedy", "Fun", "English", 7.7],

    ["Dangal", "Drama", "Inspirational", "Hindi", 8.3],
    ["Taare Zameen Par", "Drama", "Emotional", "Hindi", 8.4],
    ["The Pursuit of Happyness", "Drama", "Inspirational", "English", 8.0],
    ["The Shawshank Redemption", "Drama", "Inspirational", "English", 9.3],

    ["The Conjuring", "Horror", "Scary", "English", 7.5],
    ["Insidious", "Horror", "Scary", "English", 6.8],
    ["Hereditary", "Horror", "Dark", "English", 7.3],
    ["A Quiet Place", "Horror", "Thriller", "English", 7.5],
    ["It", "Horror", "Scary", "English", 7.3],
    ["The Exorcist", "Horror", "Scary", "English", 8.1],
    ["Get Out", "Horror", "Thriller", "English", 7.7],
    ["Scream", "Horror", "Exciting", "English", 7.4],
    ["The Ring", "Horror", "Scary", "English", 7.1],
    ["The Nun", "Horror", "Scary", "English", 5.7],

    ["The Lord of the Rings", "Fantasy", "Adventure", "English", 8.9],
    ["Harry Potter", "Fantasy", "Adventure", "English", 7.6],

    ["Pirates of the Caribbean", "Adventure", "Exciting", "English", 8.1],
    ["Jumanji", "Adventure", "Fun", "English", 6.9],

    ["Knives Out", "Mystery", "Mysterious", "English", 7.9],
    ["Gone Girl", "Mystery", "Dark", "English", 8.1],
    ["Sherlock Holmes", "Mystery", "Exciting", "English", 7.6],

    ["La La Land", "Romance", "Emotional", "English", 8.0],
    ["The Notebook", "Romance", "Emotional", "English", 7.8],
    ["Yeh Jawaani Hai Hai Deewani", "Romance", "Fun", "Hindi", 7.2],
    ["Kabir Singh", "Romance", "Emotional", "Hindi", 7.0],

    ["The Godfather", "Crime", "Dark", "English", 9.2],
    ["Goodfellas", "Crime", "Dark", "English", 8.7],
    ["Drishyam", "Crime", "Mysterious", "Hindi", 8.2],

    ["Spider-Man: Into the Spider-Verse", "Animation", "Exciting", "English", 8.4],
    ["Coco", "Animation", "Emotional", "English", 8.4],
    ["Toy Story", "Animation", "Fun", "English", 8.3],

    ["Your Name", "Animation", "Romance", "Japanese", 8.4]
], columns=["Movie", "Genre", "Mood", "Language", "Rating"])


# ============================================================
# HEADER
# ============================================================

st.title("🎬 AI Movie Recommendation System")

st.write(
    "Personalized movie recommendations using "
    "content-based preference matching."
)

st.divider()


# ============================================================
# SIDEBAR — USER PREFERENCES
# ============================================================

st.sidebar.header("🎯 Your Preferences")

genre = st.sidebar.selectbox(
    "🎭 Preferred Genre",
    ["Any"] + sorted(movies["Genre"].unique())
)

mood = st.sidebar.selectbox(
    "😊 Preferred Mood",
    ["Any"] + sorted(movies["Mood"].unique())
)

language = st.sidebar.selectbox(
    "🌐 Preferred Language",
    ["Any"] + sorted(movies["Language"].unique())
)

minimum_rating = st.sidebar.slider(
    "⭐ Minimum Rating",
    5.0,
    9.5,
    7.0,
    0.1
)

number_of_movies = st.sidebar.slider(
    "🎬 Number of Recommendations",
    3,
    10,
    5
)


# ============================================================
# DATASET INFORMATION
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("🎬 Movies", len(movies))
col2.metric("🎭 Genres", movies["Genre"].nunique())
col3.metric("😊 Moods", movies["Mood"].nunique())
col4.metric("🌐 Languages", movies["Language"].nunique())

st.divider()


# ============================================================
# DATASET PREVIEW
# ============================================================

with st.expander("📊 Explore Movie Dataset"):

    st.dataframe(
        movies,
        use_container_width=True
    )


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

if st.button(
    "✨ Generate My Recommendations",
    use_container_width=True
):

    recommendations = movies.copy()

    # --------------------------------------------------------
    # Similarity score
    # --------------------------------------------------------

    recommendations["Similarity Score"] = 0

    # --------------------------------------------------------
    # Explanation column
    # --------------------------------------------------------

    recommendations["Match Reasons"] = ""

    # --------------------------------------------------------
    # Genre match
    # --------------------------------------------------------

    if genre != "Any":

        genre_match = recommendations["Genre"] == genre

        recommendations.loc[
            genre_match,
            "Similarity Score"
        ] += 4

        recommendations.loc[
            genre_match,
            "Match Reasons"
        ] += "Genre matched • "

    # --------------------------------------------------------
    # Mood match
    # --------------------------------------------------------

    if mood != "Any":

        mood_match = recommendations["Mood"] == mood

        recommendations.loc[
            mood_match,
            "Similarity Score"
        ] += 3

        recommendations.loc[
            mood_match,
            "Match Reasons"
        ] += "Mood matched • "

    # --------------------------------------------------------
    # Language match
    # --------------------------------------------------------

    if language != "Any":

        language_match = recommendations["Language"] == language

        recommendations.loc[
            language_match,
            "Similarity Score"
        ] += 2

        recommendations.loc[
            language_match,
            "Match Reasons"
        ] += "Language matched • "

    # --------------------------------------------------------
    # Rating contribution
    # --------------------------------------------------------

    recommendations["Rating Score"] = (
        recommendations["Rating"] / 10
    )

    # --------------------------------------------------------
    # Remove movies below minimum rating
    # --------------------------------------------------------

    recommendations = recommendations[
        recommendations["Rating"] >= minimum_rating
    ]

    # --------------------------------------------------------
    # Final recommendation score
    # --------------------------------------------------------

    recommendations["Final Score"] = (
        recommendations["Similarity Score"]
        + recommendations["Rating Score"]
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    recommendations = recommendations.sort_values(
        by=["Final Score", "Rating"],
        ascending=False
    )

    top_movies = recommendations.head(number_of_movies)

    # ========================================================
    # RESULTS
    # ========================================================

    st.success(
        f"🎉 Found {len(top_movies)} movies matching your preferences!"
    )

    st.subheader("🏆 Your Personalized Recommendations")

    if len(top_movies) == 0:

        st.warning(
            "No movies match your selected rating and preferences. "
            "Try lowering the minimum rating."
        )

    else:

        for rank, (_, movie) in enumerate(
            top_movies.iterrows(),
            start=1
        ):

            # Calculate match percentage
            if movie["Similarity Score"] > 0:

                match_percentage = min(
                    int(
                        (
                            movie["Similarity Score"]
                            / 9
                        ) * 100
                    ),
                    100
                )

            else:

                match_percentage = 20

            # Movie card

            st.markdown(
                f"## #{rank} 🎬 {movie['Movie']}"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Genre",
                movie["Genre"]
            )

            c2.metric(
                "Mood",
                movie["Mood"]
            )

            c3.metric(
                "Rating",
                f"⭐ {movie['Rating']}"
            )

            c4.metric(
                "Match",
                f"{match_percentage}%"
            )

            st.progress(
                match_percentage / 100
            )

            # Recommendation explanation

            reasons = movie["Match Reasons"]

            if reasons:

                st.caption(
                    f"💡 Why recommended: {reasons.rstrip(' • ')}"
                )

            else:

                st.caption(
                    "💡 Recommended based on rating and overall ranking."
                )

            st.divider()


    # ========================================================
    # ANALYTICS
    # ========================================================

    if len(top_movies) > 0:

        st.subheader("📊 Recommendation Analysis")

        chart_data = top_movies[
            ["Movie", "Final Score"]
        ].set_index("Movie")

        st.bar_chart(
            chart_data
        )

        st.caption(
            "Higher scores indicate stronger preference alignment."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 DecodeLabs Artificial Intelligence Internship — Project 3"
)