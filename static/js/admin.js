class AdminDashboard {
    constructor() {
        this.currentGameState = null;
        this.updateInterval = null;
        this.timerInterval = null;
        this.autoProgressInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.startStatusUpdates();
    }
    
    initializeElements() {
        this.elements = {
            currentStatus: document.getElementById('currentStatus'),
            roundInfo: document.getElementById('roundInfo'),
            currentRound: document.getElementById('currentRound'),
            totalRounds: document.getElementById('totalRounds'),
            currentQuestion: document.getElementById('currentQuestion'),
            questionsPerRound: document.getElementById('questionsPerRound'),
            timeProgress: document.getElementById('timeProgress'),
            timeRemaining: document.getElementById('timeRemaining'),
            startGameBtn: document.getElementById('startGameBtn'),
            nextRoundBtn: document.getElementById('nextRoundBtn'),
            teamsContainer: document.getElementById('teamsContainer'),
            logosContainer: document.getElementById('logosContainer'),
            addLogoForm: document.getElementById('addLogoForm'),
            addLogoModal: document.getElementById('addLogoModal')
        };
    }
    
    bindEvents() {
        // Game control buttons
        if (this.elements.startGameBtn) {
            this.elements.startGameBtn.addEventListener('click', () => this.startGame());
        }
        
        if (this.elements.nextRoundBtn) {
            this.elements.nextRoundBtn.addEventListener('click', () => this.nextRound());
        }
        
        // Add logo form
        if (this.elements.addLogoForm) {
            this.elements.addLogoForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addLogo();
            });
        }
    }
    
    startStatusUpdates() {
        this.updateStatus();
        this.updateInterval = setInterval(() => {
            this.updateStatus();
        }, 2000); // Update every 2 seconds
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/admin/status');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }
            
            this.currentGameState = data;
            this.updateUI(data);
            
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }
    
    updateUI(data) {
        this.updateGameStatus(data.game);
        this.updateTeams(data.teams);
        this.updateLogos(data.logos);
    }
    
    updateGameStatus(game) {
        if (!game) {
            // No active game
            this.elements.currentStatus.textContent = 'No Active Game';
            this.elements.currentStatus.className = 'badge bg-secondary';
            this.elements.roundInfo.style.display = 'none';
            this.elements.startGameBtn.style.display = 'inline-block';
            this.elements.nextRoundBtn.style.display = 'none';
            this.clearTimer();
            return;
        }
        
        // Update status badge
        if (game.status === 'active') {
            this.elements.currentStatus.textContent = 'Game Active';
            this.elements.currentStatus.className = 'badge bg-success';
            this.elements.startGameBtn.style.display = 'none';
            this.elements.nextRoundBtn.style.display = 'none';
        } else if (game.status === 'round_complete') {
            this.elements.currentStatus.textContent = 'Round Complete - Waiting';
            this.elements.currentStatus.className = 'badge bg-warning';
            this.elements.startGameBtn.style.display = 'none';
            this.elements.nextRoundBtn.style.display = 'inline-block';
        } else if (game.status === 'finished') {
            this.elements.currentStatus.textContent = 'Game Finished';
            this.elements.currentStatus.className = 'badge bg-info';
            this.elements.startGameBtn.style.display = 'inline-block';
            this.elements.nextRoundBtn.style.display = 'none';
        }
        
        // Update round info
        if (game.status === 'active' || game.status === 'round_complete') {
            this.elements.roundInfo.style.display = 'block';
            this.elements.currentRound.textContent = game.current_round;
            this.elements.totalRounds.textContent = game.total_rounds;
            this.elements.currentQuestion.textContent = game.current_question || 1;
            this.elements.questionsPerRound.textContent = game.questions_per_round || 10;
            
            // Update timer
            this.updateTimer(game.time_remaining);
            
            // Set up automatic question progression for active games
            if (game.status === 'active') {
                this.setupAutoProgress(game.time_remaining);
            }
            
            // Update next round button
            if (game.current_round >= game.total_rounds) {
                this.elements.nextRoundBtn.innerHTML = '<i class="fas fa-flag-checkered me-2"></i>End Game';
                this.elements.nextRoundBtn.classList.remove('btn-primary');
                this.elements.nextRoundBtn.classList.add('btn-warning');
            } else {
                this.elements.nextRoundBtn.innerHTML = '<i class="fas fa-forward me-2"></i>Next Round';
                this.elements.nextRoundBtn.classList.remove('btn-warning');
                this.elements.nextRoundBtn.classList.add('btn-primary');
            }
        } else {
            this.elements.roundInfo.style.display = 'none';
            this.clearTimer();
            this.clearAutoProgress();
        }
    }
    
    setupAutoProgress(timeRemaining) {
        // Clear existing auto-progress
        this.clearAutoProgress();
        
        // Set timer to advance question when time runs out
        if (timeRemaining > 0) {
            this.autoProgressInterval = setTimeout(() => {
                this.advanceQuestion();
            }, timeRemaining * 1000);
        }
    }
    
    async advanceQuestion() {
        try {
            const response = await fetch('/api/admin/next_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update immediately
                this.updateStatus();
            }
        } catch (error) {
            console.error('Failed to advance question:', error);
        }
    }
    
    clearAutoProgress() {
        if (this.autoProgressInterval) {
            clearTimeout(this.autoProgressInterval);
            this.autoProgressInterval = null;
        }
    }
    
    updateTimer(timeRemaining) {
        const totalTime = 30;
        const progressPercent = (timeRemaining / totalTime) * 100;
        
        this.elements.timeProgress.style.width = `${progressPercent}%`;
        this.elements.timeRemaining.textContent = `${Math.ceil(timeRemaining)}s`;
        
        // Change color based on time remaining
        this.elements.timeProgress.className = 'progress-bar';
        if (timeRemaining <= 10) {
            this.elements.timeProgress.classList.add('bg-danger');
        } else if (timeRemaining <= 20) {
            this.elements.timeProgress.classList.add('bg-warning');
        } else {
            this.elements.timeProgress.classList.add('bg-success');
        }
        
        // Clear existing timer
        this.clearTimer();
        
        // Start countdown timer
        if (timeRemaining > 0) {
            this.timerInterval = setInterval(() => {
                timeRemaining--;
                const newProgressPercent = (timeRemaining / totalTime) * 100;
                this.elements.timeProgress.style.width = `${newProgressPercent}%`;
                this.elements.timeRemaining.textContent = `${Math.ceil(Math.max(0, timeRemaining))}s`;
                
                if (timeRemaining <= 0) {
                    this.clearTimer();
                }
            }, 1000);
        }
    }
    
    clearTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    updateTeams(teams) {
        if (!teams || teams.length === 0) {
            this.elements.teamsContainer.innerHTML = '<div class="text-center text-muted">No teams registered yet</div>';
            return;
        }
        
        // Sort teams by score (descending)
        const sortedTeams = teams.sort((a, b) => b.score - a.score);
        
        let html = '<div class="table-responsive"><table class="table table-striped"><thead><tr><th>Rank</th><th>Team</th><th>Members</th><th>Score</th></tr></thead><tbody>';
        
        sortedTeams.forEach((team, index) => {
            const rankIcon = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
            
            html += `
                <tr>
                    <td><strong>${rankIcon}</strong></td>
                    <td><strong>${team.name}</strong></td>
                    <td><small>${team.members.join(', ')}</small></td>
                    <td><span class="badge bg-primary">${team.score}</span></td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        this.elements.teamsContainer.innerHTML = html;
    }
    
    updateLogos(logos) {
        if (!logos || logos.length === 0) {
            this.elements.logosContainer.innerHTML = '<div class="text-center text-muted">No logos added yet</div>';
            return;
        }
        
        let html = '';
        logos.forEach(logo => {
            const alternativesList = logo.alternative_answers.length > 0 
                ? logo.alternative_answers.join(', ') 
                : 'None';
            
            html += `
                <div class="card mb-3">
                    <div class="row g-0">
                        <div class="col-md-4">
                            <img src="${logo.image_url}" class="img-fluid rounded-start h-100 object-fit-cover" 
                                 alt="${logo.name}" style="max-height: 120px; object-fit: contain;">
                        </div>
                        <div class="col-md-8">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 class="card-title">${logo.name}</h6>
                                        <p class="card-text">
                                            <small><strong>Answer:</strong> ${logo.correct_answer}</small><br>
                                            <small><strong>Alternatives:</strong> ${alternativesList}</small>
                                        </p>
                                    </div>
                                    <button class="btn btn-sm btn-outline-danger" onclick="adminDashboard.deleteLogo(${logo.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        this.elements.logosContainer.innerHTML = html;
    }
    
    async startGame() {
        try {
            this.elements.startGameBtn.disabled = true;
            this.elements.startGameBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';
            
            const response = await fetch('/api/admin/start_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update immediately
                this.updateStatus();
            } else {
                alert(data.error || 'Failed to start game');
            }
            
        } catch (error) {
            console.error('Failed to start game:', error);
            alert('Failed to start game. Please try again.');
        } finally {
            this.elements.startGameBtn.disabled = false;
            this.elements.startGameBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Game';
        }
    }
    
    async nextRound() {
        try {
            this.elements.nextRoundBtn.disabled = true;
            this.elements.nextRoundBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            
            const response = await fetch('/api/admin/next_round', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.game_finished) {
                    alert('Game finished! Final scores are displayed.');
                }
                // Update immediately
                this.updateStatus();
            } else {
                alert(data.error || 'Failed to advance round');
            }
            
        } catch (error) {
            console.error('Failed to advance round:', error);
            alert('Failed to advance round. Please try again.');
        } finally {
            this.elements.nextRoundBtn.disabled = false;
        }
    }
    
    async addLogo() {
        try {
            const logoName = document.getElementById('logoName').value.trim();
            const logoImageUrl = document.getElementById('logoImageUrl').value.trim();
            const logoCorrectAnswer = document.getElementById('logoCorrectAnswer').value.trim();
            const logoAlternatives = document.getElementById('logoAlternatives').value.trim();
            
            if (!logoName || !logoImageUrl || !logoCorrectAnswer) {
                alert('Please fill in all required fields');
                return;
            }
            
            // Parse alternatives
            const alternativeAnswers = logoAlternatives
                .split('\n')
                .map(alt => alt.trim())
                .filter(alt => alt.length > 0);
            
            const submitBtn = this.elements.addLogoForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
            
            const response = await fetch('/api/admin/logos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: logoName,
                    image_url: logoImageUrl,
                    correct_answer: logoCorrectAnswer,
                    alternative_answers: alternativeAnswers
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reset form
                this.elements.addLogoForm.reset();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(this.elements.addLogoModal);
                modal.hide();
                
                // Update logos list
                this.updateStatus();
                
                alert('Logo added successfully!');
            } else {
                alert(data.error || 'Failed to add logo');
            }
            
        } catch (error) {
            console.error('Failed to add logo:', error);
            alert('Failed to add logo. Please try again.');
        } finally {
            const submitBtn = this.elements.addLogoForm.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Add Logo';
        }
    }
    
    async deleteLogo(logoId) {
        if (!confirm('Are you sure you want to delete this logo?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/logos/${logoId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update logos list
                this.updateStatus();
                alert('Logo deleted successfully!');
            } else {
                alert(data.error || 'Failed to delete logo');
            }
            
        } catch (error) {
            console.error('Failed to delete logo:', error);
            alert('Failed to delete logo. Please try again.');
        }
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        this.clearTimer();
        this.clearAutoProgress();
    }
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.adminDashboard) {
        window.adminDashboard.destroy();
    }
});
