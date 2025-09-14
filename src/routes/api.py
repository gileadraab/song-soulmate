import os
from flask import Blueprint, request, session, jsonify
from src.services.spotify_service import SpotifyService
from src.routes.auth import get_valid_access_token

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI')
)


@api_bp.route('/user')
def get_user():
    """Get current user profile information."""
    try:
        if 'user_profile' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({'error': 'Invalid or expired token'}), 401

        return jsonify(session['user_profile'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/user/stats')
def get_user_stats():
    """Get user's music statistics."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({'error': 'Not authenticated'}), 401

        # Get user's top artists to calculate stats
        top_artists_response = spotify_service.get_top_artists(
            access_token, limit=50
        )
        top_artists = top_artists_response.get('items', [])

        # Calculate statistics
        stats = {
            'top_artists_count': len(top_artists),
            'top_genres_count': len(get_unique_genres(top_artists)),
            'music_variety': calculate_music_variety(top_artists)
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/calculate-affinity', methods=['POST'])
def calculate_affinity():
    """Calculate musical affinity between current user and target user."""
    try:
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data or 'target_user' not in data:
            return jsonify({'error': 'Target user not provided'}), 400

        target_user = data['target_user']

        # For now, return mock data since we haven't implemented the
        # affinity service yet. This will be replaced with actual affinity
        # calculation in a later commit
        mock_results = {
            'affinity_score': 75,
            'analysis': (
                f'You and {target_user} have great musical compatibility! '
                f'You share similar taste in artists and genres.'
            ),
            'common_artists': [
                {'name': 'The Beatles', 'popularity': 85},
                {'name': 'Taylor Swift', 'popularity': 90},
                {'name': 'Ed Sheeran', 'popularity': 88}
            ],
            'common_genres': ['pop', 'rock', 'indie'],
            'metrics': {
                'artist_similarity': '78%',
                'genre_similarity': '72%',
                'popularity_similarity': '85%',
                'overall_match': '75%'
            }
        }

        return jsonify(mock_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_unique_genres(artists):
    """Extract unique genres from a list of artists."""
    genres = set()
    for artist in artists:
        if 'genres' in artist:
            genres.update(artist['genres'])
    return list(genres)


def calculate_music_variety(artists):
    """Calculate music variety score based on genre diversity."""
    if not artists:
        return 'Unknown'

    genres = get_unique_genres(artists)
    genre_count = len(genres)

    if genre_count >= 10:
        return 'Very High'
    elif genre_count >= 7:
        return 'High'
    elif genre_count >= 4:
        return 'Medium'
    elif genre_count >= 2:
        return 'Low'
    else:
        return 'Very Low'
