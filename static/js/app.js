// SongSoulmate Frontend Application
class SongSoulmate {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
        this.handleAuthCallback();
    }

    bindEvents() {
        // Authentication buttons
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');
        
        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.login());
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        // Affinity calculation form
        const affinityForm = document.getElementById('affinity-form');
        if (affinityForm) {
            affinityForm.addEventListener('submit', (e) => this.handleAffinityCalculation(e));
        }

        // New calculation button
        const newCalculationBtn = document.getElementById('new-calculation-btn');
        if (newCalculationBtn) {
            newCalculationBtn.addEventListener('click', () => this.resetCalculation());
        }
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/user', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.setAuthenticatedState(userData);
            } else {
                this.setUnauthenticatedState();
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            this.setUnauthenticatedState();
        }
    }

    handleAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
            this.showError('Authentication failed: ' + error);
            this.setUnauthenticatedState();
            return;
        }

        if (code) {
            this.exchangeCodeForToken(code);
        }
    }

    async exchangeCodeForToken(code) {
        try {
            this.showLoading('Authenticating with Spotify...');
            
            const response = await fetch('/auth/callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code }),
                credentials: 'include'
            });

            if (response.ok) {
                const userData = await response.json();
                this.setAuthenticatedState(userData);
                this.showSuccess('Successfully connected to Spotify!');
                
                // Clean up URL
                window.history.replaceState({}, document.title, window.location.pathname);
            } else {
                const errorData = await response.json();
                this.showError('Authentication failed: ' + errorData.error);
                this.setUnauthenticatedState();
            }
        } catch (error) {
            console.error('Error during token exchange:', error);
            this.showError('Authentication failed. Please try again.');
            this.setUnauthenticatedState();
        } finally {
            this.hideLoading();
        }
    }

    async login() {
        try {
            const response = await fetch('/auth/login');
            const data = await response.json();
            
            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                this.showError('Failed to initiate authentication');
            }
        } catch (error) {
            console.error('Error during login:', error);
            this.showError('Login failed. Please try again.');
        }
    }

    async logout() {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            this.setUnauthenticatedState();
            this.showSuccess('Successfully logged out');
        } catch (error) {
            console.error('Error during logout:', error);
            this.showError('Logout failed');
        }
    }

    setAuthenticatedState(userData) {
        this.isAuthenticated = true;
        this.currentUser = userData;

        // Update UI elements
        const loginBtn = document.getElementById('login-btn');
        const userInfo = document.getElementById('user-info');
        const welcomeSection = document.getElementById('welcome-section');
        const appSection = document.getElementById('app-section');

        if (loginBtn) loginBtn.style.display = 'none';
        if (userInfo) userInfo.style.display = 'flex';
        if (welcomeSection) welcomeSection.style.display = 'none';
        if (appSection) appSection.style.display = 'block';

        // Update user info display
        this.updateUserInfo(userData);
        this.loadUserStats();
    }

    setUnauthenticatedState() {
        this.isAuthenticated = false;
        this.currentUser = null;

        // Update UI elements
        const loginBtn = document.getElementById('login-btn');
        const userInfo = document.getElementById('user-info');
        const welcomeSection = document.getElementById('welcome-section');
        const appSection = document.getElementById('app-section');

        if (loginBtn) loginBtn.style.display = 'block';
        if (userInfo) userInfo.style.display = 'none';
        if (welcomeSection) welcomeSection.style.display = 'block';
        if (appSection) appSection.style.display = 'none';
    }

    updateUserInfo(userData) {
        const userName = document.getElementById('user-name');
        const userAvatar = document.getElementById('user-avatar');

        if (userName) {
            userName.textContent = userData.display_name || userData.id;
        }

        if (userAvatar && userData.images && userData.images.length > 0) {
            userAvatar.src = userData.images[0].url;
            userAvatar.alt = userData.display_name || userData.id;
        }
    }

    async loadUserStats() {
        try {
            const response = await fetch('/api/user/stats', {
                credentials: 'include'
            });

            if (response.ok) {
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const topArtistsCount = document.getElementById('top-artists-count');
        const topGenresCount = document.getElementById('top-genres-count');
        const musicVariety = document.getElementById('music-variety');

        if (topArtistsCount) {
            topArtistsCount.textContent = stats.top_artists_count || '0';
        }

        if (topGenresCount) {
            topGenresCount.textContent = stats.top_genres_count || '0';
        }

        if (musicVariety) {
            musicVariety.textContent = stats.music_variety || 'Unknown';
        }
    }

    async handleAffinityCalculation(event) {
        event.preventDefault();
        
        const targetUserInput = document.getElementById('target-user');
        const targetUser = targetUserInput.value.trim();

        if (!targetUser) {
            this.showError('Please enter a target user');
            return;
        }

        this.setCalculationLoading(true);

        try {
            const response = await fetch('/api/calculate-affinity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ target_user: targetUser }),
                credentials: 'include'
            });

            if (response.ok) {
                const results = await response.json();
                this.displayResults(results);
            } else {
                const errorData = await response.json();
                this.showError('Calculation failed: ' + errorData.error);
            }
        } catch (error) {
            console.error('Error calculating affinity:', error);
            this.showError('Failed to calculate affinity. Please try again.');
        } finally {
            this.setCalculationLoading(false);
        }
    }

    displayResults(results) {
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }

        // Update affinity score with animation
        this.animateScore(results.affinity_score);
        
        // Update score description
        const affinityTitle = document.getElementById('affinity-title');
        const affinityDescription = document.getElementById('affinity-description');
        
        if (affinityTitle) {
            affinityTitle.textContent = this.getAffinityTitle(results.affinity_score);
        }
        
        if (affinityDescription) {
            affinityDescription.textContent = results.analysis || this.getAffinityDescription(results.affinity_score);
        }

        // Display common artists
        this.displayCommonArtists(results.common_artists || []);
        
        // Display common genres
        this.displayCommonGenres(results.common_genres || []);
        
        // Display compatibility metrics
        this.displayCompatibilityMetrics(results.metrics || {});

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    animateScore(score) {
        const scoreNumber = document.getElementById('affinity-score');
        const progressBar = document.getElementById('score-progress-bar');
        const circumference = 2 * Math.PI * 45; // radius = 45

        if (scoreNumber) {
            // Animate number counting
            let currentScore = 0;
            const increment = score / 50; // 50 frames for animation
            const timer = setInterval(() => {
                currentScore += increment;
                if (currentScore >= score) {
                    currentScore = score;
                    clearInterval(timer);
                }
                scoreNumber.textContent = Math.round(currentScore);
            }, 20);
        }

        if (progressBar) {
            // Animate progress circle
            const offset = circumference - (score / 100) * circumference;
            progressBar.style.strokeDashoffset = offset;
        }
    }

    displayCommonArtists(artists) {
        const container = document.getElementById('common-artists');
        if (!container) return;

        container.innerHTML = '';
        
        if (artists.length === 0) {
            container.innerHTML = '<p class="no-data">No common artists found</p>';
            return;
        }

        artists.forEach(artist => {
            const artistElement = document.createElement('span');
            artistElement.className = 'artist-item';
            artistElement.textContent = artist.name || artist;
            container.appendChild(artistElement);
        });
    }

    displayCommonGenres(genres) {
        const container = document.getElementById('common-genres');
        if (!container) return;

        container.innerHTML = '';
        
        if (genres.length === 0) {
            container.innerHTML = '<p class="no-data">No common genres found</p>';
            return;
        }

        genres.forEach(genre => {
            const genreElement = document.createElement('span');
            genreElement.className = 'genre-item';
            genreElement.textContent = genre;
            container.appendChild(genreElement);
        });
    }

    displayCompatibilityMetrics(metrics) {
        const container = document.getElementById('compatibility-metrics');
        if (!container) return;

        container.innerHTML = '';

        const metricsData = [
            { label: 'Artist Overlap', value: metrics.artist_similarity || '0%' },
            { label: 'Genre Similarity', value: metrics.genre_similarity || '0%' },
            { label: 'Popularity Match', value: metrics.popularity_similarity || '0%' },
            { label: 'Overall Match', value: metrics.overall_match || '0%' }
        ];

        metricsData.forEach(metric => {
            const metricElement = document.createElement('div');
            metricElement.className = 'metric-item';
            metricElement.innerHTML = `
                <span class="metric-label">${metric.label}</span>
                <span class="metric-value">${metric.value}</span>
            `;
            container.appendChild(metricElement);
        });
    }

    getAffinityTitle(score) {
        if (score >= 80) return '🎵 Musical Soulmates!';
        if (score >= 60) return '🎶 Great Compatibility';
        if (score >= 40) return '🎵 Some Common Ground';
        if (score >= 20) return '🎶 Different Tastes';
        return '🎵 Opposite Tastes';
    }

    getAffinityDescription(score) {
        if (score >= 80) return 'You two have incredibly similar music taste! You\'d make great playlist collaborators.';
        if (score >= 60) return 'You share quite a bit of musical common ground. You\'d enjoy discovering music together.';
        if (score >= 40) return 'You have some shared musical interests, but also enjoy different styles.';
        if (score >= 20) return 'Your music tastes are quite different, but that could lead to interesting discoveries.';
        return 'You have very different music preferences, which could make for exciting musical exploration together.';
    }

    setCalculationLoading(isLoading) {
        const submitBtn = document.querySelector('#affinity-form button[type="submit"]');
        const btnText = submitBtn?.querySelector('.btn-text');
        const spinner = submitBtn?.querySelector('.loading-spinner');

        if (submitBtn) {
            submitBtn.disabled = isLoading;
        }

        if (btnText) {
            btnText.textContent = isLoading ? 'Calculating...' : 'Calculate Affinity';
        }

        if (spinner) {
            spinner.style.display = isLoading ? 'block' : 'none';
        }
    }

    resetCalculation() {
        const resultsSection = document.getElementById('results-section');
        const targetUserInput = document.getElementById('target-user');

        if (resultsSection) {
            resultsSection.style.display = 'none';
        }

        if (targetUserInput) {
            targetUserInput.value = '';
            targetUserInput.focus();
        }

        // Reset score animation
        const progressBar = document.getElementById('score-progress-bar');
        if (progressBar) {
            progressBar.style.strokeDashoffset = '283';
        }

        const scoreNumber = document.getElementById('affinity-score');
        if (scoreNumber) {
            scoreNumber.textContent = '0';
        }
    }

    showLoading(message) {
        // You can implement a global loading indicator here
        console.log('Loading:', message);
    }

    hideLoading() {
        // Hide global loading indicator
        console.log('Loading complete');
    }

    showError(message) {
        // You can implement a toast notification system here
        console.error('Error:', message);
        alert(message); // Temporary solution
    }

    showSuccess(message) {
        // You can implement a toast notification system here
        console.log('Success:', message);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SongSoulmate();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SongSoulmate;
}