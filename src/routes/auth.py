import os
from flask import Blueprint, request, redirect, url_for, session, flash, jsonify
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
        return redirect(auth_url)
    except Exception as e:
        flash(f'Error initiating login: {str(e)}', 'error')
        return redirect(url_for('index'))


@auth_bp.route('/callback')
def callback():
    """Handle Spotify OAuth callback."""
    try:
        # Verify state parameter to prevent CSRF attacks
        state = request.args.get('state')
        if not state or state != session.get('oauth_state'):
            flash('Invalid state parameter. Please try logging in again.', 'error')
            return redirect(url_for('index'))
        
        # Check for authorization errors
        error = request.args.get('error')
        if error:
            flash(f'Spotify authorization error: {error}', 'error')
            return redirect(url_for('index'))
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            flash('No authorization code received from Spotify.', 'error')
            return redirect(url_for('index'))
        
        # Exchange code for access token
        token_data = spotify_service.get_access_token(code)
        
        # Store token data in session
        session['spotify_token'] = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': token_data['expires_at'].isoformat() if token_data.get('expires_at') else None,
            'token_type': token_data.get('token_type', 'Bearer')
        }
        
        # Get user profile to store basic info
        user_profile = spotify_service.get_user_profile(token_data['access_token'])
        session['user_profile'] = {
            'id': user_profile['id'],
            'display_name': user_profile.get('display_name', 'Unknown User'),
            'email': user_profile.get('email'),
            'images': user_profile.get('images', [])
        }
        
        # Clear oauth state
        session.pop('oauth_state', None)
        
        flash(f'Successfully logged in as {user_profile.get("display_name", "Unknown User")}!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error during authentication: {str(e)}', 'error')
        return redirect(url_for('index'))


@auth_bp.route('/logout')
def logout():
    """Log out the user by clearing session data."""
    try:
        session.clear()
        flash('Successfully logged out!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error during logout: {str(e)}', 'error')
        return redirect(url_for('index'))


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
                        new_token_data = spotify_service.refresh_access_token(token_data['refresh_token'])
                        session['spotify_token'].update({
                            'access_token': new_token_data['access_token'],
                            'expires_at': new_token_data['expires_at'].isoformat()
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
                        'message': 'Token expired and no refresh token available'
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
            new_token_data = spotify_service.refresh_access_token(token_data['refresh_token'])
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