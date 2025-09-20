import os

from flask import Blueprint, jsonify, request, session

from src.routes.auth import get_valid_access_token
from src.services.affinity_service import AffinityService
from src.services.spotify_service import SpotifyService
from src.utils.cache import cache_affinity_result, cache_user_stats

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

        # Use cached version of stats calculation
        stats = _get_cached_user_stats(access_token)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cache_user_stats(expire=900)  # Cache for 15 minutes
def _get_cached_user_stats(access_token):
    """Cached helper function to calculate user statistics."""
    # Get user's top artists to calculate stats
    top_artists_response = spotify_service.get_top_artists(access_token, limit=50)
    top_artists = top_artists_response.get("items", [])

    # Calculate statistics
    stats = {
        "top_artists_count": len(top_artists),
        "top_genres_count": len(get_unique_genres(top_artists)),
        "music_variety": calculate_music_variety(top_artists),
    }

    return stats


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

        # Use cached affinity calculation
        affinity_results = _get_cached_affinity_calculation(access_token, target_user)

        if "error" in affinity_results:
            if affinity_results["error"].startswith("Unable to find music data"):
                return jsonify(affinity_results), 404
            else:
                return jsonify(affinity_results), 400

        return jsonify(affinity_results)

    except Exception as e:
        return jsonify({"error": f"Failed to calculate affinity: {str(e)}"}), 500


@cache_affinity_result(expire=3600)  # Cache for 1 hour
def _get_cached_affinity_calculation(access_token, target_user):
    """Cached helper function to calculate affinity between users."""
    try:
        # Get current user's top artists
        current_user_response = spotify_service.get_top_artists(access_token, limit=50)
        current_user_artists = current_user_response.get("items", [])

        if not current_user_artists:
            return {
                "error": (
                    "Unable to fetch your music data. Please make sure you "
                    "have listening history on Spotify."
                )
            }

        # Get target user artists (supports both real Spotify URLs and mock users)
        target_user_artists = get_target_user_artists(target_user, access_token)

        if not target_user_artists:
            # Check if it was a URL to provide a more specific error message
            user_id = spotify_service.extract_user_id_from_url(target_user)
            if user_id and user_id != target_user:
                return {
                    "error": (
                        f"Unable to find public music data for Spotify user "
                        f"'{user_id}'. Their profile may be private, they may not "
                        "have public playlists, or the user doesn't exist. "
                        "Try using demo users: john, sarah, mike, or alex."
                    )
                }
            else:
                return {
                    "error": (
                        f"Unable to find music data for user '{target_user}'. "
                        "Try using a Spotify profile URL "
                        "(https://open.spotify.com/user/USERNAME) or demo users: "
                        "john, sarah, mike, or alex."
                    )
                }

        # Calculate affinity using the affinity service
        affinity_results = affinity_service.calculate_affinity(
            current_user_artists, target_user_artists
        )

        # Add target user info to the results
        affinity_results["target_user"] = target_user

        return affinity_results

    except Exception as e:
        return {"error": f"Failed to calculate affinity: {str(e)}"}


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


def get_target_user_artists(target_user, access_token):
    """
    Get artist data for a target user. Supports both mock users and real
    Spotify URLs/IDs.

    Args:
        target_user (str): Username, Spotify URL, or user ID
        access_token (str): Valid Spotify access token

    Returns:
        list: List of artist data or None if user not found
    """
    # First try to extract user ID from URL if it's a Spotify URL
    user_id = spotify_service.extract_user_id_from_url(target_user)

    if user_id and user_id != target_user:
        # It was a URL and we extracted the ID, try to get real data
        try:
            # Check if user profile exists and is public
            user_profile = spotify_service.get_user_profile_by_id(user_id, access_token)
            if user_profile:
                # Try to get artist data from their public playlists
                artists = spotify_service.get_user_top_tracks_from_playlists(
                    user_id, access_token
                )
                if artists:
                    return artists
                else:
                    # No public playlists or no tracks found
                    return None
            else:
                # User profile is private or doesn't exist
                return None
        except Exception as e:
            print(f"Error fetching real user data: {e}")
            return None

    # If it wasn't a URL or real data fetch failed, try mock data
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
    return mock_users.get(target_user.lower())


@api_bp.route("/cache/clear", methods=["POST"])
def clear_user_cache():
    """Clear cache for the current user."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401

        # Invalidate user-specific cache
        spotify_service.invalidate_user_cache(access_token)

        return jsonify({"message": "User cache cleared successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cache/warm", methods=["POST"])
def warm_cache():
    """Pre-warm cache with user data."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Not authenticated"}), 401

        # Pre-fetch and cache user data
        spotify_service.get_user_profile(access_token)
        spotify_service.get_top_artists(access_token, limit=50)
        _get_cached_user_stats(access_token)

        return jsonify({"message": "Cache warmed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
