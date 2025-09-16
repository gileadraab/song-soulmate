import math
from collections import Counter
from typing import List, Dict, Any, Tuple


class AffinityService:
    """
    Service for calculating musical affinity between users based on their
    Spotify listening data.
    """

    def __init__(self):
        self.weights = {
            "common_artists": 0.4,  # 40% weight for shared artists
            "genre_similarity": 0.3,  # 30% weight for genre overlap
            "popularity_similarity": 0.2,  # 20% weight for popularity alignment
            "artist_diversity": 0.1,  # 10% weight for musical diversity
        }

    def calculate_affinity(
        self, user1_artists: List[Dict], user2_artists: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive musical affinity between two users.

        Args:
            user1_artists: List of artist dictionaries for user 1
            user2_artists: List of artist dictionaries for user 2

        Returns:
            dict: Comprehensive affinity analysis with score and metrics
        """
        if not user1_artists or not user2_artists:
            return self._create_empty_result()

        # Calculate individual metrics
        common_artists = self.find_common_artists(user1_artists, user2_artists)
        common_artist_score = len(common_artists) / max(
            len(user1_artists), len(user2_artists)
        )

        genre_similarity_score = self.calculate_genre_similarity(
            user1_artists, user2_artists
        )

        popularity_similarity_score = self.calculate_popularity_similarity(
            user1_artists, user2_artists
        )

        diversity_score = self.calculate_diversity_compatibility(
            user1_artists, user2_artists
        )

        # Calculate weighted overall score
        overall_score = (
            common_artist_score * self.weights["common_artists"]
            + genre_similarity_score * self.weights["genre_similarity"]
            + popularity_similarity_score * self.weights["popularity_similarity"]
            + diversity_score * self.weights["artist_diversity"]
        )

        # Convert to percentage and round
        affinity_percentage = round(overall_score * 100)

        # Generate analysis text
        analysis = self.generate_analysis(
            affinity_percentage, len(common_artists), user1_artists, user2_artists
        )

        # Get common genres
        common_genres = self.find_common_genres(user1_artists, user2_artists)

        return {
            "affinity_score": affinity_percentage,
            "analysis": analysis,
            "common_artists": [
                {"name": artist["name"], "popularity": artist.get("popularity", 0)}
                for artist in common_artists
            ],
            "common_genres": common_genres,
            "metrics": {
                "artist_similarity": f"{round(common_artist_score * 100)}%",
                "genre_similarity": f"{round(genre_similarity_score * 100)}%",
                "popularity_similarity": f"{round(popularity_similarity_score * 100)}%",
                "overall_match": f"{affinity_percentage}%",
            },
            "detailed_scores": {
                "common_artists": round(common_artist_score * 100),
                "genre_similarity": round(genre_similarity_score * 100),
                "popularity_similarity": round(popularity_similarity_score * 100),
                "diversity_compatibility": round(diversity_score * 100),
            },
        }

    def find_common_artists(
        self, artists1: List[Dict], artists2: List[Dict]
    ) -> List[Dict]:
        """
        Find artists that appear in both users' top artists lists.

        Args:
            artists1: First user's artists
            artists2: Second user's artists

        Returns:
            list: Common artists with their data
        """
        artists1_ids = {artist["id"]: artist for artist in artists1}
        artists2_ids = {artist["id"] for artist in artists2}

        common_artists = []
        for artist_id in artists1_ids:
            if artist_id in artists2_ids:
                common_artists.append(artists1_ids[artist_id])

        return common_artists

    def calculate_genre_similarity(
        self, artists1: List[Dict], artists2: List[Dict]
    ) -> float:
        """
        Calculate genre similarity using Jaccard index.

        Args:
            artists1: First user's artists
            artists2: Second user's artists

        Returns:
            float: Genre similarity score (0-1)
        """
        genres1 = self._extract_genres(artists1)
        genres2 = self._extract_genres(artists2)

        if not genres1 or not genres2:
            return 0.0

        # Calculate Jaccard index
        intersection = len(genres1.intersection(genres2))
        union = len(genres1.union(genres2))

        return intersection / union if union > 0 else 0.0

    def calculate_popularity_similarity(
        self, artists1: List[Dict], artists2: List[Dict]
    ) -> float:
        """
        Calculate similarity in artist popularity preferences.

        Args:
            artists1: First user's artists
            artists2: Second user's artists

        Returns:
            float: Popularity similarity score (0-1)
        """
        pop1 = [artist.get("popularity", 50) for artist in artists1]
        pop2 = [artist.get("popularity", 50) for artist in artists2]

        if not pop1 or not pop2:
            return 0.0

        avg_pop1 = sum(pop1) / len(pop1)
        avg_pop2 = sum(pop2) / len(pop2)

        # Calculate similarity based on average popularity difference
        max_diff = 100  # Maximum possible difference in popularity
        actual_diff = abs(avg_pop1 - avg_pop2)
        similarity = 1 - (actual_diff / max_diff)

        return max(0.0, similarity)

    def calculate_diversity_compatibility(
        self, artists1: List[Dict], artists2: List[Dict]
    ) -> float:
        """
        Calculate compatibility based on musical diversity.

        Args:
            artists1: First user's artists
            artists2: Second user's artists

        Returns:
            float: Diversity compatibility score (0-1)
        """
        diversity1 = self._calculate_genre_diversity(artists1)
        diversity2 = self._calculate_genre_diversity(artists2)

        # Higher score if both users have similar diversity levels
        diversity_diff = abs(diversity1 - diversity2)
        max_diversity_diff = 1.0

        return 1 - (diversity_diff / max_diversity_diff)

    def find_common_genres(
        self, artists1: List[Dict], artists2: List[Dict]
    ) -> List[str]:
        """
        Find genres that appear in both users' artist lists.

        Args:
            artists1: First user's artists
            artists2: Second user's artists

        Returns:
            list: Common genres sorted by frequency
        """
        genres1 = self._extract_genres(artists1)
        genres2 = self._extract_genres(artists2)

        common_genres = genres1.intersection(genres2)
        return sorted(list(common_genres))

    def generate_analysis(
        self,
        score: int,
        common_count: int,
        user1_artists: List[Dict],
        user2_artists: List[Dict],
    ) -> str:
        """
        Generate human-readable analysis based on affinity score.

        Args:
            score: Affinity score percentage
            common_count: Number of common artists
            user1_artists: First user's artists
            user2_artists: Second user's artists

        Returns:
            str: Analysis text
        """
        if score >= 85:
            compatibility = "exceptional musical compatibility"
            description = "You're practically musical soulmates!"
        elif score >= 70:
            compatibility = "great musical compatibility"
            description = "You have a lot in common musically."
        elif score >= 55:
            compatibility = "good musical compatibility"
            description = "You share some interesting musical preferences."
        elif score >= 40:
            compatibility = "moderate musical compatibility"
            description = "You have some overlapping tastes, but also unique preferences."
        elif score >= 25:
            compatibility = "limited musical compatibility"
            description = "Your musical tastes are quite different, but that's not bad!"
        else:
            compatibility = "very different musical preferences"
            description = "You each have unique musical styles - variety is the spice of life!"

        common_text = ""
        if common_count > 0:
            if common_count == 1:
                common_text = f" You share {common_count} common artist."
            else:
                common_text = f" You share {common_count} common artists."

        return f"You have {compatibility}! {description}{common_text}"

    def _extract_genres(self, artists: List[Dict]) -> set:
        """Extract unique genres from artists list."""
        genres = set()
        for artist in artists:
            if "genres" in artist and artist["genres"]:
                genres.update(artist["genres"])
        return genres

    def _calculate_genre_diversity(self, artists: List[Dict]) -> float:
        """Calculate genre diversity using Shannon diversity index."""
        genres = []
        for artist in artists:
            if "genres" in artist and artist["genres"]:
                genres.extend(artist["genres"])

        if not genres:
            return 0.0

        # Count genre frequencies
        genre_counts = Counter(genres)
        total_genres = len(genres)

        # Calculate Shannon diversity index
        diversity = 0.0
        for count in genre_counts.values():
            proportion = count / total_genres
            diversity -= proportion * math.log2(proportion)

        # Normalize to 0-1 range
        max_diversity = math.log2(len(genre_counts)) if len(genre_counts) > 1 else 1
        return diversity / max_diversity if max_diversity > 0 else 0.0

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result for cases with no data."""
        return {
            "affinity_score": 0,
            "analysis": "Unable to calculate affinity - insufficient data.",
            "common_artists": [],
            "common_genres": [],
            "metrics": {
                "artist_similarity": "0%",
                "genre_similarity": "0%",
                "popularity_similarity": "0%",
                "overall_match": "0%",
            },
            "detailed_scores": {
                "common_artists": 0,
                "genre_similarity": 0,
                "popularity_similarity": 0,
                "diversity_compatibility": 0,
            },
        }