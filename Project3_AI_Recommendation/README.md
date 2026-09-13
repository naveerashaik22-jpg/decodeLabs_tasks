# 🎬 AI Movie Recommendation System

## 📌 Project Overview

This project is a simple AI-based movie recommendation system developed as part of the **Artificial Intelligence Internship at DecodeLabs**.

The system recommends movies based on user preferences such as **genre, mood, language, and minimum rating**. It uses preference matching and a similarity-based scoring approach to rank the most relevant movies.

## 🎯 Objective

The objective of this project is to create a simple recommendation system that:

- Takes user preferences as input
- Matches preferences with movie attributes
- Calculates a similarity score
- Ranks movies based on preference alignment
- Displays personalized recommendations

## ⚙️ How It Works

The recommendation system follows these steps:

1. User selects their preferred genre.
2. User selects a preferred mood.
3. User selects a preferred language.
4. User chooses a minimum movie rating.
5. The system compares these preferences with the movie dataset.
6. Matching attributes receive similarity points.
7. Movies are ranked using the final score.
8. The highest-ranked movies are displayed as personalized recommendations.

## 🧠 Recommendation Logic

The system assigns points based on matching preferences:

| Preference | Score |
|------------|-------|
| Genre Match | +4 |
| Mood Match | +3 |
| Language Match | +2 |

A rating contribution is also included in the final recommendation score.

### Final Score

```text
Final Score = Similarity Score + Rating Score