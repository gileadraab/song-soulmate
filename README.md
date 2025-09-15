# SongSoulmate

A musical affinity calculator that analyzes your Spotify listening habits to find your perfect musical match.

## What it does

Connect your Spotify account and discover how compatible your music taste is with friends. SongSoulmate analyzes your favorite artists, genres, and listening patterns to calculate a comprehensive musical affinity score.

## Features

- **Artist Analysis** - Compare top artists and discover shared musical preferences
- **Genre Compatibility** - Analyze genre overlap and musical style similarities  
- **Affinity Score** - Get a detailed compatibility breakdown with visual metrics

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: HTML, CSS, JavaScript
- **API**: Spotify Web API
- **Authentication**: OAuth 2.0

## Quick Start

1. Clone the repository
2. Set up your environment variables in `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python app.py`

## Configuration

Create a `.env` file with your Spotify app credentials:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/auth/callback
SECRET_KEY=your_secret_key
```
# Docker Support
