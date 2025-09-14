# SongSoulmate - Plano de Implementação Python

## 🎯 Visão Geral
Implementação incremental usando Python + Flask, dividida em branches e commits organizados para facilitar o processo de CI/CD.

## 🐍 Stack Tecnológica
- **Backend**: Python + Flask
- **Frontend**: HTML + CSS + JavaScript (vanilla)
- **API**: Spotify Web API
- **Testes**: pytest
- **Autenticação**: OAuth 2.0 (Spotify)

## 📋 Estrutura de Branches e Commits

### **Branch 1: `feature/project-setup`**
Configuração inicial do projeto Python.

#### Commit 1: "Initial Python project setup"
```bash
# Comandos para Claude Code:
# "Create a Python Flask project structure for TuneSync Spotify affinity calculator"
# "Set up requirements.txt with Flask, requests, python-dotenv, pytest"
# "Create virtual environment setup and basic folder structure"
```

**Arquivos criados:**
- `requirements.txt`
- `app.py` (arquivo principal)
- `.gitignore` (Python)
- `README.md`
- `.env.example`
- Estrutura de pastas

**Estrutura do projeto:**
```
tunesync/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── spotify_service.py
│   │   └── affinity_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
└── tests/
    ├── __init__.py
    ├── test_spotify_service.py
    ├── test_affinity_service.py
    └── conftest.py
```

#### Commit 2: "Add Flask application with basic routes"
```bash
# "Create basic Flask app with health check and static file serving"
# "Add environment configuration and error handling"
# "Set up basic logging and development server"
```

**Arquivos criados/modificados:**
- `app.py`
- `src/__init__.py`
- `src/routes/__init__.py`

#### Commit 3: "Add frontend templates and static files"
```bash
# "Create Jinja2 templates for the main page"
# "Add CSS with Spotify-like design and responsive layout"
# "Create basic JavaScript for frontend interactions"
```

**Arquivos criados:**
- `templates/index.html`
- `static/css/style.css`
- `static/js/app.js`

---

### **Branch 2: `feature/spotify-auth`**
Implementação da autenticação com Spotify usando OAuth.

#### Commit 4: "Implement Spotify OAuth service"
```bash
# "Create SpotifyService class with OAuth authorization flow"
# "Add methods for getting auth URL and exchanging code for token"
# "Implement token validation and refresh functionality"
```

**Arquivos criados:**
- `src/services/spotify_service.py`

**Código exemplo:**
```python
import requests
import base64
from urllib.parse import urlencode

class SpotifyService:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"
```

#### Commit 5: "Add authentication routes"
```bash
# "Create Flask routes for login, callback, and logout"
# "Implement session management for storing tokens"
# "Add error handling for authentication failures"
```

**Arquivos criados:**
- `src/routes/auth.py`

#### Commit 6: "Integrate frontend authentication"
```bash
# "Add login button and authentication flow to frontend"
# "Implement JavaScript for handling auth callbacks"
# "Add user session display and logout functionality"
```

**Arquivos modificados:**
- `templates/index.html`
- `static/js/app.js`
- `static/css/style.css`

---

### **Branch 3: `feature/spotify-api`**
Integração completa com a API do Spotify.

#### Commit 7: "Implement user data fetching"
```bash
# "Add methods to fetch user profile and top artists"
# "Implement error handling for API rate limits"
# "Add data caching and normalization"
```

**Arquivos modificados:**
- `src/services/spotify_service.py`

**Métodos principais:**
```python
def get_user_profile(self, access_token):
def get_top_artists(self, access_token, limit=20, time_range='medium_term'):
def get_user_playlists(self, access_token):
```

#### Commit 8: "Add mock data for demo purposes"
```bash
# "Create mock artist data for testing and demo"
# "Implement user simulation for comparison feature"
# "Add realistic genre and popularity data"
```

**Arquivos criados:**
- `src/utils/mock_data.py`

#### Commit 9: "Create API routes for user data"
```bash
# "Add Flask routes to serve user's top artists"
# "Implement JSON API endpoints for frontend consumption"
# "Add proper HTTP status codes and error responses"
```

**Arquivos criados:**
- `src/routes/api.py`

---

### **Branch 4: `feature/affinity-algorithm`**
Algoritmo de cálculo de afinidade musical em Python.

#### Commit 10: "Create affinity calculation service"
```bash
# "Implement AffinityService with core algorithm logic"
# "Add methods for artist comparison and genre analysis"
# "Calculate weighted scores based on multiple factors"
```

**Arquivos criados:**
- `src/services/affinity_service.py`

**Estrutura da classe:**
```python
class AffinityService:
    def calculate_affinity(self, user1_artists, user2_artists):
    def find_common_artists(self, artists1, artists2):
    def calculate_genre_similarity(self, artists1, artists2):
    def calculate_popularity_similarity(self, artists1, artists2):
    def generate_analysis(self, score, common_count):
```

#### Commit 11: "Add advanced similarity metrics"
```bash
# "Implement cosine similarity for artist vectors"
# "Add Jaccard index for genre comparison"
# "Create comprehensive scoring breakdown"
```

**Arquivos modificados:**
- `src/services/affinity_service.py`

#### Commit 12: "Add comprehensive tests for affinity"
```bash
# "Create pytest tests for all affinity calculations"
# "Add test fixtures with mock artist data"
# "Test edge cases and error handling"
```

**Arquivos criados:**
- `tests/test_affinity_service.py`
- `tests/conftest.py`

---

### **Branch 5: `feature/web-interface`**
Interface web completa para interação do usuário.

#### Commit 13: "Add affinity calculation API endpoint"
```bash
# "Create POST endpoint for affinity calculation"
# "Integrate SpotifyService with AffinityService"
# "Add input validation and error handling"
```

**Arquivos modificados:**
- `src/routes/api.py`
- `app.py`

#### Commit 14: "Implement affinity calculation UI"
```bash
# "Add form for target user input"
# "Create loading states and progress indicators"
# "Implement real-time affinity calculation"
```

**Arquivos modificados:**
- `templates/index.html`
- `static/js/app.js`

#### Commit 15: "Add results visualization"
```bash
# "Create results page with score visualization"
# "Display common artists and genres with styling"
# "Add charts and progress bars for metrics"
```

**Arquivos modificados:**
- `templates/index.html`
- `static/css/style.css`
- `static/js/app.js`

---

### **Branch 6: `feature/enhancements`**
Melhorias finais e otimizações.

#### Commit 16: "Add caching and performance optimization"
```bash
# "Implement Redis/memory caching for API responses"
# "Add request rate limiting and optimization"
# "Optimize database queries and API calls"
```

**Arquivos criados/modificados:**
- `src/utils/cache.py`
- `requirements.txt` (adicionar redis)

#### Commit 17: "Add comprehensive error handling"
```bash
# "Implement custom exception classes"
# "Add user-friendly error pages and messages"
# "Create logging system for debugging"
```

**Arquivos criados:**
- `src/utils/exceptions.py`
- `src/utils/logger.py`

#### Commit 18: "Add final tests and documentation"
```bash
# "Create integration tests for complete flow"
# "Add API documentation and code comments"
# "Create deployment configuration"
```

**Arquivos criados:**
- `tests/test_integration.py`
- `docs/API.md`
- `Procfile` (para Heroku)

---

## 🐍 **Comandos específicos para Claude Code**

### Configuração inicial:
```bash
mkdir tunesync
cd tunesync
git init
git checkout -b feature/project-setup

# Usar Claude Code
claude-code "Create a Python Flask project for TuneSync Spotify affinity calculator. Include requirements.txt with Flask, requests, python-dotenv, pytest. Create proper Python project structure with src/ folder"
```

### Exemplos de comandos por commit:

#### Commit 1:
```bash
claude-code "Create requirements.txt for Flask web app with dependencies: Flask, requests, python-dotenv, pytest, flask-session. Add .gitignore for Python projects and basic project structure"
```

#### Commit 4:
```bash
claude-code "Create SpotifyService class in Python with methods: get_auth_url(), get_access_token(code), get_top_artists(token). Use requests library for HTTP calls and include error handling"
```

#### Commit 10:
```bash
claude-code "Create AffinityService class with calculate_affinity method that compares two lists of artist dictionaries. Include methods for finding common artists, calculating genre similarity, and generating analysis text"
```

## 📦 **requirements.txt**
```txt
Flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.2
flask-session==0.5.0
redis==4.6.0
gunicorn==21.2.0
```

## 🔧 **Configuração do ambiente**

### 1. Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Variáveis de ambiente (.env):
```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/auth/callback
FLASK_ENV=development
FLASK_SECRET_KEY=your_secret_key
```

## 🧪 **Estrutura de Testes**

### conftest.py:
```python
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_artists():
    return [
        {
            "id": "1",
            "name": "The Beatles",
            "popularity": 85,
            "genres": ["rock", "pop"]
        }
    ]
```

## 🚀 **Como executar**

### Desenvolvimento:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Testes:
```bash
pytest tests/ -v
pytest --cov=src tests/
```

## 🎯 **Próximos passos para CI/CD**

1. **GitHub Actions** com Python
2. **Deploy no Heroku** com Procfile
3. **Code coverage** com pytest-cov
4. **Linting** com flake8/black
5. **Security scanning** com bandit

Quer que eu detalhe algum commit específico ou ajude com a configuração inicial do projeto Python?
