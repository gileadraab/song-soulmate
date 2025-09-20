import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests

from src.utils.cache import cache_spotify_response


class SpotifyService:
    """
    Service for handling Spotify Web API authentication and data retrieval.
    """

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"

    def get_auth_url(self, scopes=None):
        """
        Generate Spotify authorization URL for OAuth flow.

        Args:
            scopes (list): List of required Spotify scopes

        Returns:
            tuple: (auth_url, state) - URL for authorization and state
                parameter
        """
        if scopes is None:
            scopes = ["user-top-read", "user-read-private"]

        state = secrets.token_urlsafe(16)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "show_dialog": "true",
        }

        auth_url = f"{self.auth_url}?{urlencode(params)}"
        return auth_url, state

    def get_access_token(self, authorization_code):
        """
        Exchange authorization code for access token.

        Args:
            authorization_code (str): Authorization code from callback

        Returns:
            dict: Token response with access_token, refresh_token, expires_in
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(self.token_url, headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            # Add expiration timestamp
            expires_in = token_data["expires_in"]
            token_data["expires_at"] = datetime.now() + timedelta(seconds=expires_in)
            return token_data
        else:
            error_msg = (
                f"Error getting access token: {response.status_code} - "
                f"{response.text}"
            )
            raise Exception(error_msg)

    def refresh_access_token(self, refresh_token):
        """
        Refresh expired access token using refresh token.

        Args:
            refresh_token (str): Refresh token from previous authentication

        Returns:
            dict: New token response with access_token and expires_in
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        response = requests.post(self.token_url, headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            # Add expiration timestamp
            expires_in = token_data["expires_in"]
            token_data["expires_at"] = datetime.now() + timedelta(seconds=expires_in)
            return token_data
        else:
            error_msg = (
                f"Error refreshing access token: {response.status_code} - "
                f"{response.text}"
            )
            raise Exception(error_msg)

    def is_token_valid(self, token_data):
        """
        Check if access token is still valid.

        Args:
            token_data (dict): Token data with expires_at timestamp

        Returns:
            bool: True if token is valid, False if expired
        """
        if not token_data or "expires_at" not in token_data:
            return False

        expires_at = token_data["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        # Add 5 minute buffer before expiration
        return datetime.now() < (expires_at - timedelta(minutes=5))

    def validate_token(self, access_token):
        """
        Validate access token by making a test API call.

        Args:
            access_token (str): Spotify access token

        Returns:
            bool: True if token is valid, False otherwise
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(f"{self.api_base_url}/me", headers=headers)
        return response.status_code == 200

    @cache_spotify_response(expire=1800)  # Cache for 30 minutes
    def get_user_profile(self, access_token):
        """
        Get current user's profile information.

        Args:
            access_token (str): Valid Spotify access token

        Returns:
            dict: User profile data
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(f"{self.api_base_url}/me", headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = (
                f"Error getting user profile: {response.status_code} - "
                f"{response.text}"
            )
            raise Exception(error_msg)

    @cache_spotify_response(expire=900)  # Cache for 15 minutes
    def get_top_artists(self, access_token, limit=20, time_range="medium_term"):
        """
        Get user's top artists from Spotify.

        Args:
            access_token (str): Valid Spotify access token
            limit (int): Number of artists to retrieve (max 50)
            time_range (str): Time range for top artists
                ('short_term', 'medium_term', 'long_term')

        Returns:
            dict: Top artists data from Spotify API
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        params = {
            "limit": min(limit, 50),  # Spotify API limit is 50
            "time_range": time_range,
        }

        response = requests.get(
            f"{self.api_base_url}/me/top/artists", headers=headers, params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = (
                f"Error getting top artists: {response.status_code} - "
                f"{response.text}"
            )
            raise Exception(error_msg)

    def get_user_id_from_token(self, access_token):
        """
        Extract user ID from access token for cache key generation.

        Args:
            access_token (str): Valid Spotify access token

        Returns:
            str: User ID hash for cache key
        """
        try:
            user_profile = self.get_user_profile(access_token)
            user_id = user_profile.get("id", "unknown")
            # Create hash of user ID for privacy
            return hashlib.md5(user_id.encode()).hexdigest()[:8]
        except Exception:
            # Fallback to token hash if profile fetch fails
            return hashlib.md5(access_token.encode()).hexdigest()[:8]

    def extract_user_id_from_url(self, spotify_url):
        """
        Extract user ID from Spotify profile URL.

        Args:
            spotify_url (str): Spotify profile URL or user ID

        Returns:
            str: Extracted user ID or None if invalid
        """
        if not spotify_url:
            return None

        # If it's already just a user ID, return it
        if not spotify_url.startswith("http"):
            return spotify_url.strip()

        # Parse Spotify URL formats:
        # https://open.spotify.com/user/USERNAME
        # https://open.spotify.com/user/USERNAME?si=...
        if "open.spotify.com/user/" in spotify_url:
            try:
                # Extract user ID from URL
                parts = spotify_url.split("/user/")[1]
                user_id = parts.split("?")[0]  # Remove query parameters
                return user_id.strip()
            except (IndexError, AttributeError):
                return None

        return None

    @cache_spotify_response(expire=1800)  # Cache for 30 minutes
    def get_user_public_playlists(self, user_id, access_token, limit=20):
        """
        Get user's public playlists to check if profile is accessible.

        Args:
            user_id (str): Spotify user ID
            access_token (str): Valid Spotify access token
            limit (int): Number of playlists to retrieve

        Returns:
            dict: User's public playlists or None if private/not found
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        params = {"limit": min(limit, 50)}

        response = requests.get(
            f"{self.api_base_url}/users/{user_id}/playlists",
            headers=headers,
            params=params,
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # User not found
        elif response.status_code == 403:
            return None  # Private profile
        else:
            # Other errors
            return None

    @cache_spotify_response(expire=1800)  # Cache for 30 minutes
    def get_user_profile_by_id(self, user_id, access_token):
        """
        Get public user profile by user ID.

        Args:
            user_id (str): Spotify user ID
            access_token (str): Valid Spotify access token

        Returns:
            dict: User profile data or None if not accessible
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(f"{self.api_base_url}/users/{user_id}", headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # User not found
        else:
            return None  # Other errors (private, etc.)

    def get_user_top_tracks_from_playlists(self, user_id, access_token, limit=50):
        """
        Try to analyze user's music taste from their public playlists.
        This is a workaround since we can't directly access other users' top artists.

        Args:
            user_id (str): Spotify user ID
            access_token (str): Valid Spotify access token
            limit (int): Number of tracks to analyze

        Returns:
            list: List of artist data extracted from public playlists
        """
        try:
            # Get user's public playlists
            playlists_response = self.get_user_public_playlists(user_id, access_token)
            if not playlists_response or not playlists_response.get("items"):
                return []

            headers = {"Authorization": f"Bearer {access_token}"}
            artists_data = {}
            track_count = 0

            # Analyze tracks from public playlists
            for playlist in playlists_response["items"][:5]:  # Check first 5 playlists
                if track_count >= limit:
                    break

                playlist_id = playlist["id"]
                tracks_response = requests.get(
                    f"{self.api_base_url}/playlists/{playlist_id}/tracks",
                    headers=headers,
                    params={"limit": min(20, limit - track_count)},
                )

                if tracks_response.status_code == 200:
                    tracks_data = tracks_response.json()
                    for item in tracks_data.get("items", []):
                        if track_count >= limit:
                            break

                        track = item.get("track")
                        if track and track.get("artists"):
                            for artist in track["artists"]:
                                artist_id = artist["id"]
                                if artist_id not in artists_data:
                                    # Get detailed artist info
                                    artist_response = requests.get(
                                        f"{self.api_base_url}/artists/{artist_id}",
                                        headers=headers,
                                    )
                                    if artist_response.status_code == 200:
                                        artist_data = artist_response.json()
                                        artists_data[artist_id] = {
                                            "id": artist_data["id"],
                                            "name": artist_data["name"],
                                            "popularity": artist_data.get(
                                                "popularity", 0
                                            ),
                                            "genres": artist_data.get("genres", []),
                                        }

                        track_count += 1

            # Convert to list and sort by popularity
            artists_list = list(artists_data.values())
            artists_list.sort(key=lambda x: x["popularity"], reverse=True)

            return artists_list[:20]  # Return top 20 artists by popularity

        except Exception as e:
            print(f"Error analyzing user playlists: {e}")
            return []

    def invalidate_user_cache(self, access_token):
        """
        Invalidate cache for a specific user when their data changes.

        Args:
            access_token (str): User's access token
        """
        from src.utils.cache import invalidate_user_cache

        user_id = self.get_user_id_from_token(access_token)
        invalidate_user_cache(user_id)
