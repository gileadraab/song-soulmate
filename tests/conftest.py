from unittest.mock import Mock

import pytest

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SPOTIFY_CLIENT_ID": "test-client-id",
        "SPOTIFY_CLIENT_SECRET": "test-client-secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:5000/auth/callback",
    }

    app = create_app(test_config)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_spotify_response():
    """Mock Spotify API response data."""
    return {
        "items": [
            {
                "id": "4Z8W4fKeB5YxbusRsdQVPb",
                "name": "Radiohead",
                "popularity": 82,
                "genres": [
                    "alternative rock",
                    "art rock",
                    "melancholia",
                    "oxford indie",
                    "permanent wave",
                    "rock",
                ],
            },
            {
                "id": "6FBDaR13swtiWwGhX1WQsP",
                "name": "blink-182",
                "popularity": 79,
                "genres": ["pop punk", "rock", "socal pop punk"],
            },
        ]
    }


@pytest.fixture
def mock_user_profile():
    """Mock user profile data."""
    return {
        "id": "test_user_123",
        "display_name": "Test User",
        "email": "test@example.com",
        "images": [
            {"url": "https://example.com/avatar.jpg", "height": 64, "width": 64}
        ],
        "followers": {"total": 100},
        "country": "US",
    }


@pytest.fixture
def mock_access_token():
    """Mock access token."""
    return "mock_access_token_12345"


@pytest.fixture
def mock_artists():
    """Fixture providing sample artist data for testing."""
    return [
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


@pytest.fixture
def mock_spotify_service():
    """Mock SpotifyService for testing."""
    mock_service = Mock()

    # Mock the get_top_artists method
    mock_service.get_top_artists.return_value = {
        "items": [
            {
                "id": "1",
                "name": "Test Artist",
                "popularity": 75,
                "genres": ["rock", "alternative"],
            }
        ]
    }

    # Mock the get_user_profile method
    mock_service.get_user_profile.return_value = {
        "id": "test_user",
        "display_name": "Test User",
        "email": "test@example.com",
    }

    return mock_service


@pytest.fixture
def authenticated_session(client, mock_user_profile, mock_access_token):
    """Create an authenticated session for testing."""
    with client.session_transaction() as session:
        session["access_token"] = mock_access_token
        session["refresh_token"] = "mock_refresh_token"
        session["user_profile"] = mock_user_profile
        session["token_expires_at"] = 9999999999  # Far future timestamp

    return session


class TestUtils:
    """Utility class for test helpers."""

    @staticmethod
    def create_mock_artists(count=5, base_popularity=75):
        """Create mock artist data for testing."""
        artists = []
        genres_pool = [
            ["rock", "alternative"],
            ["pop", "dance"],
            ["hip hop", "rap"],
            ["jazz", "blues"],
            ["electronic", "ambient"],
            ["country", "folk"],
            ["metal", "hardcore"],
            ["indie", "experimental"],
        ]

        for i in range(count):
            artist = {
                "id": f"artist_{i}",
                "name": f"Test Artist {i}",
                "popularity": base_popularity + (i * 2),
                "genres": genres_pool[i % len(genres_pool)],
            }
            artists.append(artist)

        return artists

    @staticmethod
    def create_mock_affinity_result(score=75):
        """Create mock affinity calculation result."""
        return {
            "affinity_score": score,
            "analysis": (
                "You have great musical compatibility! "
                "You share some interesting musical preferences."
            ),
            "common_artists": [
                {"name": "Common Artist 1", "popularity": 80},
                {"name": "Common Artist 2", "popularity": 75},
            ],
            "common_genres": ["rock", "alternative"],
            "metrics": {
                "artist_similarity": f"{score - 10}%",
                "genre_similarity": f"{score - 5}%",
                "popularity_similarity": f"{score + 5}%",
                "overall_match": f"{score}%",
            },
            "detailed_scores": {
                "common_artists": score - 10,
                "genre_similarity": score - 5,
                "popularity_similarity": score + 5,
                "diversity_compatibility": score,
            },
        }


# Make TestUtils available as a fixture
@pytest.fixture
def test_utils():
    """Provide test utility functions."""
    return TestUtils
