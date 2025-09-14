import requests
import base64
import secrets
from urllib.parse import urlencode
from datetime import datetime, timedelta


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
