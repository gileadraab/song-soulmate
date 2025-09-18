from src.services.affinity_service import AffinityService


class TestAffinityService:
    """Test suite for the AffinityService class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.affinity_service = AffinityService()

        # Sample artist data for testing
        self.sample_artists_1 = [
            {
                "id": "1",
                "name": "The Beatles",
                "popularity": 85,
                "genres": ["rock", "pop", "british invasion"],
            },
            {
                "id": "2",
                "name": "Radiohead",
                "popularity": 82,
                "genres": ["alternative rock", "art rock", "rock"],
            },
            {
                "id": "3",
                "name": "Pink Floyd",
                "popularity": 80,
                "genres": ["progressive rock", "rock", "psychedelic rock"],
            },
        ]

        self.sample_artists_2 = [
            {
                "id": "1",
                "name": "The Beatles",
                "popularity": 85,
                "genres": ["rock", "pop", "british invasion"],
            },
            {
                "id": "4",
                "name": "Led Zeppelin",
                "popularity": 83,
                "genres": ["hard rock", "rock", "blues rock"],
            },
            {
                "id": "5",
                "name": "Taylor Swift",
                "popularity": 100,
                "genres": ["pop", "country"],
            },
        ]

    def test_calculate_affinity_with_valid_data(self):
        """Test affinity calculation with valid artist data."""
        result = self.affinity_service.calculate_affinity(
            self.sample_artists_1, self.sample_artists_2
        )

        # Check that result has expected structure
        assert "affinity_score" in result
        assert "analysis" in result
        assert "common_artists" in result
        assert "common_genres" in result
        assert "metrics" in result
        assert "detailed_scores" in result

        # Check that score is a number between 0 and 100
        assert isinstance(result["affinity_score"], int)
        assert 0 <= result["affinity_score"] <= 100

        # Check that analysis is a string
        assert isinstance(result["analysis"], str)
        assert len(result["analysis"]) > 0

    def test_calculate_affinity_with_empty_lists(self):
        """Test affinity calculation with empty artist lists."""
        result = self.affinity_service.calculate_affinity([], [])

        assert result["affinity_score"] == 0
        assert "insufficient data" in result["analysis"].lower()
        assert result["common_artists"] == []
        assert result["common_genres"] == []

    def test_calculate_affinity_with_one_empty_list(self):
        """Test affinity calculation when one list is empty."""
        result = self.affinity_service.calculate_affinity(self.sample_artists_1, [])

        assert result["affinity_score"] == 0
        assert "insufficient data" in result["analysis"].lower()

    def test_find_common_artists(self):
        """Test finding common artists between two lists."""
        common = self.affinity_service.find_common_artists(
            self.sample_artists_1, self.sample_artists_2
        )

        # Should find The Beatles (id: "1") as common
        assert len(common) == 1
        assert common[0]["id"] == "1"
        assert common[0]["name"] == "The Beatles"

    def test_find_common_artists_no_overlap(self):
        """Test finding common artists when there's no overlap."""
        artists_no_overlap = [
            {"id": "99", "name": "Unique Artist", "popularity": 50, "genres": ["indie"]}
        ]

        common = self.affinity_service.find_common_artists(
            self.sample_artists_1, artists_no_overlap
        )

        assert len(common) == 0

    def test_calculate_genre_similarity(self):
        """Test genre similarity calculation using Jaccard index."""
        similarity = self.affinity_service.calculate_genre_similarity(
            self.sample_artists_1, self.sample_artists_2
        )

        # Should be a float between 0 and 1
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1

        # With rock and pop overlap, should be > 0
        assert similarity > 0

    def test_calculate_genre_similarity_no_genres(self):
        """Test genre similarity when artists have no genres."""
        artists_no_genres = [{"id": "1", "name": "Artist 1", "popularity": 50}]

        similarity = self.affinity_service.calculate_genre_similarity(
            artists_no_genres, artists_no_genres
        )

        assert similarity == 0.0

    def test_calculate_popularity_similarity(self):
        """Test popularity similarity calculation."""
        similarity = self.affinity_service.calculate_popularity_similarity(
            self.sample_artists_1, self.sample_artists_2
        )

        # Should be a float between 0 and 1
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1

    def test_calculate_popularity_similarity_identical(self):
        """Test popularity similarity with identical popularity values."""
        identical_artists = [
            {"id": "1", "name": "Artist 1", "popularity": 80},
            {"id": "2", "name": "Artist 2", "popularity": 80},
        ]

        similarity = self.affinity_service.calculate_popularity_similarity(
            identical_artists, identical_artists
        )

        # Should be very high (close to 1.0)
        assert similarity > 0.9

    def test_calculate_diversity_compatibility(self):
        """Test diversity compatibility calculation."""
        diversity = self.affinity_service.calculate_diversity_compatibility(
            self.sample_artists_1, self.sample_artists_2
        )

        # Should be a float between 0 and 1
        assert isinstance(diversity, float)
        assert 0 <= diversity <= 1

    def test_find_common_genres(self):
        """Test finding common genres between artist lists."""
        common_genres = self.affinity_service.find_common_genres(
            self.sample_artists_1, self.sample_artists_2
        )

        # Should find "rock" and "pop" as common genres
        assert "rock" in common_genres
        assert "pop" in common_genres
        assert len(common_genres) >= 2

    def test_generate_analysis_high_score(self):
        """Test analysis generation for high affinity scores."""
        analysis = self.affinity_service.generate_analysis(
            90, 5, self.sample_artists_1, self.sample_artists_2
        )

        assert "exceptional" in analysis.lower() or "soulmate" in analysis.lower()
        assert "5 common artists" in analysis

    def test_generate_analysis_low_score(self):
        """Test analysis generation for low affinity scores."""
        analysis = self.affinity_service.generate_analysis(
            15, 0, self.sample_artists_1, self.sample_artists_2
        )

        assert "different" in analysis.lower() or "limited" in analysis.lower()

    def test_generate_analysis_single_common_artist(self):
        """Test analysis generation with single common artist."""
        analysis = self.affinity_service.generate_analysis(
            50, 1, self.sample_artists_1, self.sample_artists_2
        )

        assert "1 common artist" in analysis

    def test_extract_genres_private_method(self):
        """Test the private _extract_genres method."""
        genres = self.affinity_service._extract_genres(self.sample_artists_1)

        expected_genres = {
            "rock",
            "pop",
            "british invasion",
            "alternative rock",
            "art rock",
            "progressive rock",
            "psychedelic rock",
        }

        assert genres == expected_genres

    def test_extract_genres_empty_list(self):
        """Test _extract_genres with empty list."""
        genres = self.affinity_service._extract_genres([])
        assert genres == set()

    def test_extract_genres_no_genre_field(self):
        """Test _extract_genres with artists missing genre field."""
        artists_no_genres = [{"id": "1", "name": "Artist 1", "popularity": 50}]

        genres = self.affinity_service._extract_genres(artists_no_genres)
        assert genres == set()

    def test_calculate_genre_diversity_private_method(self):
        """Test the private _calculate_genre_diversity method."""
        diversity = self.affinity_service._calculate_genre_diversity(
            self.sample_artists_1
        )

        # Should be a float between 0 and 1
        assert isinstance(diversity, float)
        assert 0 <= diversity <= 1

        # With multiple genres, should be > 0
        assert diversity > 0

    def test_calculate_genre_diversity_no_genres(self):
        """Test _calculate_genre_diversity with no genres."""
        artists_no_genres = [{"id": "1", "name": "Artist 1", "popularity": 50}]

        diversity = self.affinity_service._calculate_genre_diversity(artists_no_genres)

        assert diversity == 0.0

    def test_create_empty_result_private_method(self):
        """Test the private _create_empty_result method."""
        result = self.affinity_service._create_empty_result()

        # Check structure
        assert result["affinity_score"] == 0
        assert "insufficient data" in result["analysis"].lower()
        assert result["common_artists"] == []
        assert result["common_genres"] == []
        assert all(value == "0%" for value in result["metrics"].values())
        assert all(value == 0 for value in result["detailed_scores"].values())

    def test_metrics_structure(self):
        """Test that metrics have the expected structure."""
        result = self.affinity_service.calculate_affinity(
            self.sample_artists_1, self.sample_artists_2
        )

        metrics = result["metrics"]
        expected_keys = {
            "artist_similarity",
            "genre_similarity",
            "popularity_similarity",
            "overall_match",
        }

        assert set(metrics.keys()) == expected_keys

        # All values should end with '%'
        for value in metrics.values():
            assert value.endswith("%")

    def test_detailed_scores_structure(self):
        """Test that detailed scores have the expected structure."""
        result = self.affinity_service.calculate_affinity(
            self.sample_artists_1, self.sample_artists_2
        )

        detailed_scores = result["detailed_scores"]
        expected_keys = {
            "common_artists",
            "genre_similarity",
            "popularity_similarity",
            "diversity_compatibility",
        }

        assert set(detailed_scores.keys()) == expected_keys

        # All values should be integers between 0 and 100
        for value in detailed_scores.values():
            assert isinstance(value, int)
            assert 0 <= value <= 100

    def test_edge_case_identical_artists(self):
        """Test edge case where both users have identical artists."""
        result = self.affinity_service.calculate_affinity(
            self.sample_artists_1, self.sample_artists_1
        )

        # Should have very high affinity
        assert result["affinity_score"] >= 80
        assert len(result["common_artists"]) == len(self.sample_artists_1)

    def test_edge_case_very_different_popularity(self):
        """Test edge case with very different popularity ranges."""
        low_pop_artists = [
            {
                "id": "1",
                "name": "Indie Artist",
                "popularity": 10,
                "genres": ["indie", "experimental"],
            }
        ]

        high_pop_artists = [
            {
                "id": "2",
                "name": "Mainstream Artist",
                "popularity": 100,
                "genres": ["pop", "mainstream"],
            }
        ]

        result = self.affinity_service.calculate_affinity(
            low_pop_artists, high_pop_artists
        )

        # Should still produce valid result
        assert 0 <= result["affinity_score"] <= 100
        assert isinstance(result["analysis"], str)
