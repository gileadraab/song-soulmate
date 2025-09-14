import os
from flask import Blueprint, request, redirect, session, jsonify
from src.services.spotify_service import SpotifyService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize Spotify service
spotify_service = SpotifyService(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI')
)


@auth_bp.route('/login')
def login():
    """Initiate Spotify OAuth login flow."""
    try:
        auth_url, state = spotify_service.get_auth_url()
        session['oauth_state'] = state
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/callback', methods=['GET', 'POST'])
def callback():
    """Handle Spotify OAuth callback."""
    try:
        if request.method == 'GET':
            # Handle direct callback from Spotify (redirect to frontend)
            error = request.args.get('error')
            if error:
                return redirect(f'/?error={error}')

            code = request.args.get('code')
            if not code:
                return redirect('/?error=no_code')

            return redirect(f'/?code={code}')

        elif request.method == 'POST':
            # Handle AJAX request from frontend
            data = request.get_json()
            if not data or 'code' not in data:
                error_msg = 'No authorization code provided'
                return jsonify({'error': error_msg}), 400

            code = data['code']

            # Exchange code for access token
            token_data = spotify_service.get_access_token(code)

            # Store token data in session
            session['spotify_token'] = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': (
                    token_data['expires_at'].isoformat()
                    if token_data.get('expires_at') else None
                ),
                'token_type': token_data.get('token_type', 'Bearer')
            }

            # Get user profile to store basic info
            access_token = token_data['access_token']
            user_profile = spotify_service.get_user_profile(access_token)
            session['user_profile'] = {
                'id': user_profile['id'],
                'display_name': user_profile.get(
                    'display_name', 'Unknown User'
                ),
                'email': user_profile.get('email'),
                'images': user_profile.get('images', [])
            }

            # Clear oauth state
            session.pop('oauth_state', None)

            return jsonify(session['user_profile'])

    except Exception as e:
        if request.method == 'POST':
            return jsonify({'error': str(e)}), 500
        else:
            return redirect('/?error=auth_failed')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the user by clearing session data."""
    try:
        session.clear()
        return jsonify({'message': 'Successfully logged out'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/status')
def status():
    """Check authentication status."""
    try:
        if 'spotify_token' in session and 'user_profile' in session:
            token_data = session['spotify_token']

            # Check if token is still valid
            if spotify_service.is_token_valid(token_data):
                return jsonify({
                    'authenticated': True,
                    'user': session['user_profile'],
                    'token_valid': True
                })
            else:
                # Try to refresh the token
                if token_data.get('refresh_token'):
                    try:
                        refresh_token = token_data['refresh_token']
                        new_token_data = spotify_service.refresh_access_token(
                            refresh_token
                        )
                        session['spotify_token'].update({
                            'access_token': new_token_data['access_token'],
                            'expires_at': (
                                new_token_data['expires_at'].isoformat()
                            )
                        })
                        return jsonify({
                            'authenticated': True,
                            'user': session['user_profile'],
                            'token_valid': True,
                            'token_refreshed': True
                        })
                    except Exception:
                        # Refresh failed, user needs to re-authenticate
                        session.clear()
                        return jsonify({
                            'authenticated': False,
                            'token_valid': False,
                            'message': 'Token expired and refresh failed'
                        })
                else:
                    # No refresh token, user needs to re-authenticate
                    session.clear()
                    return jsonify({
                        'authenticated': False,
                        'token_valid': False,
                        'message': (
                            'Token expired and no refresh token available'
                        )
                    })
        else:
            return jsonify({
                'authenticated': False,
                'token_valid': False,
                'message': 'Not authenticated'
            })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500


def get_valid_access_token():
    """Helper function to get a valid access token from session."""
    if 'spotify_token' not in session:
        return None

    token_data = session['spotify_token']

    # Check if token is still valid
    if spotify_service.is_token_valid(token_data):
        return token_data['access_token']

    # Try to refresh the token
    if token_data.get('refresh_token'):
        try:
            refresh_token = token_data['refresh_token']
            new_token_data = spotify_service.refresh_access_token(
                refresh_token
            )
            session['spotify_token'].update({
                'access_token': new_token_data['access_token'],
                'expires_at': new_token_data['expires_at'].isoformat()
            })
            return new_token_data['access_token']
        except Exception:
            # Refresh failed, clear session
            session.clear()
            return None

    return None
