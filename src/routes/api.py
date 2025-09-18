import os
from flask import Blueprint, request, session, jsonify
from src.services.spotify_service import SpotifyService
from src.services.affinity_service import AffinityService
from src.routes.auth import get_valid_access_token

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Initialize services
spotify_service = SpotifyService(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
)
affinity_service = AffinityService()


@api_bp.route("/user")
def get_user():
    """Get current user profile information."""
    try:
        if "user_profile" not in session:
            return jsonify({"error": "Not authenticated"}), 401

        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify(session["user_profile"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/user/stats")
def get_user_stats():
    """Get user's music statistics."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401

        # Get user's top artists to calculate stats
        top_artists_response = spotify_service.get_top_artists(access_token, limit=50)
        top_artists = top_artists_response.get("items", [])

        # Calculate statistics
        stats = {
            "top_artists_count": len(top_artists),
            "top_genres_count": len(get_unique_genres(top_artists)),
            "music_variety": calculate_music_variety(top_artists),
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/calculate-affinity", methods=["POST"])
def calculate_affinity():
    """Calculate musical affinity between current user and target user."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401

        data = request.get_json()
        if not data or "target_user" not in data:
            return jsonify({"error": "Target user not provided"}), 400

        target_user = data["target_user"].strip()
        if not target_user:
            return jsonify({"error": "Target user cannot be empty"}), 400

        # Get current user's top artists
        current_user_response = spotify_service.get_top_artists(access_token, limit=50)
        current_user_artists = current_user_response.get("items", [])

        if not current_user_artists:
            return (
                jsonify(
                    {
                        "error": (
                            "Unable to fetch your music data. Please make sure you "
                            "have listening history on Spotify."
                        )
                    }
                ),
                400,
            )

        # For demo purposes, we'll use mock data for the target user
        # In a real implementation, this would search for the target user
        # and fetch their top artists (if their profile is public)
        target_user_artists = get_mock_user_artists(target_user)

        if not target_user_artists:
            return (
                jsonify(
                    {
                        "error": (
                            f"Unable to find music data for user '{target_user}'. "
                            "They may have a private profile or don't exist."
                        )
                    }
                ),
                404,
            )

        # Calculate affinity using the affinity service
        affinity_results = affinity_service.calculate_affinity(
            current_user_artists, target_user_artists
        )

        # Add target user info to the results
        affinity_results["target_user"] = target_user

        return jsonify(affinity_results)

    except Exception as e:
        return jsonify({"error": f"Failed to calculate affinity: {str(e)}"}), 500


def get_unique_genres(artists):
    """Extract unique genres from a list of artists."""
    genres = set()
    for artist in artists:
        if "genres" in artist:
            genres.update(artist["genres"])
    return list(genres)


def calculate_music_variety(artists):
    """Calculate music variety score based on genre diversity."""
    if not artists:
        return "Unknown"

    genres = get_unique_genres(artists)
    genre_count = len(genres)

    if genre_count >= 10:
        return "Very High"
    elif genre_count >= 7:
        return "High"
    elif genre_count >= 4:
        return "Medium"
    elif genre_count >= 2:
        return "Low"
    else:
        return "Very Low"


def get_mock_user_artists(username):
    """
    Get mock artist data for a target user for demo purposes.
    In a real implementation, this would fetch actual user data from Spotify API.
    """
    # Mock data based on different user types for demo
    mock_users = {
        "john": [
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
            {
                "id": "4NHQUGzhtTLFvgF5SZesLK",
                "name": "Tame Impala",
                "popularity": 81,
                "genres": ["australian psych", "neo-psychedelic", "psychedelic rock"],
            },
            {
                "id": "0L8ExT028jH3ddEcZwqJJ5",
                "name": "Red Hot Chili Peppers",
                "popularity": 84,
                "genres": [
                    "alternative rock",
                    "funk metal",
                    "funk rock",
                    "permanent wave",
                    "rock",
                ],
            },
            {
                "id": "2ye2Wgw4gimLv2eAKyk1NB",
                "name": "Metallica",
                "popularity": 85,
                "genres": [
                    "hard rock",
                    "metal",
                    "old school thrash",
                    "rock",
                    "thrash metal",
                ],
            },
        ],
        "sarah": [
            {
                "id": "06HL4z0CvFAxyc27GXpf02",
                "name": "Taylor Swift",
                "popularity": 100,
                "genres": ["pop", "country"],
            },
            {
                "id": "1uNFoZAHBGtllmzznpCI3s",
                "name": "Justin Bieber",
                "popularity": 90,
                "genres": ["canadian pop", "pop"],
            },
            {
                "id": "66CXWjxzNUsdJxJ2JdwvnR",
                "name": "Ariana Grande",
                "popularity": 91,
                "genres": ["dance pop", "pop"],
            },
            {
                "id": "4q3ewBCX7sLwd24euuV69X",
                "name": "Ed Sheeran",
                "popularity": 90,
                "genres": ["pop", "uk pop"],
            },
            {
                "id": "1McMsnEElThX1knmY9oliG",
                "name": "Olivia Rodrigo",
                "popularity": 87,
                "genres": ["pop", "teen pop"],
            },
        ],
        "mike": [
            {
                "id": "4dpARuHxo51G3z768sgnrY",
                "name": "Adele",
                "popularity": 84,
                "genres": ["british soul", "pop", "uk pop"],
            },
            {
                "id": "3TVXtAsR1Inumwj472S9r4",
                "name": "Drake",
                "popularity": 96,
                "genres": ["canadian hip hop", "hip hop", "rap"],
            },
            {
                "id": "7dGJo4pcD2V6oG8kP0tJRR",
                "name": "Eminem",
                "popularity": 91,
                "genres": ["detroit hip hop", "hip hop", "rap"],
            },
            {
                "id": "2YZyLoL8N0Wb9xBt1NhZWg",
                "name": "Kendrick Lamar",
                "popularity": 89,
                "genres": ["conscious hip hop", "hip hop", "rap", "west coast rap"],
            },
            {
                "id": "1Xyo4u8uXC1ZmMpatF05PJ",
                "name": "The Weeknd",
                "popularity": 94,
                "genres": ["canadian contemporary r&b", "canadian pop", "pop"],
            },
        ],
        "alex": [
            {
                "id": "6vWDO969PvNqNYHIOW5v0m",
                "name": "Beyoncé",
                "popularity": 86,
                "genres": ["dance pop", "pop", "r&b"],
            },
            {
                "id": "3fMbdgg4jU18AjLCKBhRSm",
                "name": "Michael Jackson",
                "popularity": 85,
                "genres": ["pop", "post-disco", "rock", "soul"],
            },
            {
                "id": "181bsRPaVXVlUKXrxwZfHK",
                "name": "Muse",
                "popularity": 79,
                "genres": ["alternative rock", "modern rock", "permanent wave", "rock"],
            },
            {
                "id": "7jy3rLJdDQY21OgRLCZ9sD",
                "name": "Foo Fighters",
                "popularity": 78,
                "genres": [
                    "alternative rock",
                    "grunge",
                    "permanent wave",
                    "post-grunge",
                    "rock",
                ],
            },
            {
                "id": "53XhwfbYqKCa1cC15pYq2q",
                "name": "Imagine Dragons",
                "popularity": 85,
                "genres": ["modern rock", "pop", "rock"],
            },
        ],
    }

    # Return mock data if user exists, otherwise None
    return mock_users.get(username.lower())
