class TeamDashboard {
    constructor(teamName) {
        this.teamName = teamName;
        this.currentGameState = null;
        this.updateInterval = null;
        this.timerInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.startStatusUpdates();
    }
    
    initializeElements() {
        this.elements = {
            waitingMessage: document.getElementById('waitingMessage'),
            gameActive: document.getElementById('gameActive'),
            gameFinished: document.getElementById('gameFinished'),
            roundInfo: document.getElementById('roundInfo'),
            timeRemaining: document.getElementById('timeRemaining'),
            currentLogo: document.getElementById('currentLogo'),
            guessForm: document.getElementById('guessForm'),
            guessInput: document.getElementById('guessInput'),
            submitBtn: document.getElementById('submitBtn'),
            guessStatus: document.getElementById('guessStatus'),
            guessAlert: document.getElementById('guessAlert'),
            guessMessage: document.getElementById('guessMessage'),
            teamScore: document.getElementById('teamScore'),
            finalScore: document.getElementById('finalScore'),
            leaderboard: document.getElementById('leaderboard')
        };
    }
    
    bindEvents() {
        if (this.elements.guessForm) {
            this.elements.guessForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitGuess();
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
            const response = await fetch(`/api/status/${encodeURIComponent(this.teamName)}`);
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
    
    updateUI(gameState) {
        // Update score
        if (this.elements.teamScore) {
            this.elements.teamScore.textContent = gameState.team_score;
        }
        
        // Update game status
        if (gameState.game_status === 'waiting') {
            this.showWaitingState();
        } else if (gameState.game_status === 'active') {
            this.showActiveGame(gameState);
        } else if (gameState.game_status === 'finished') {
            this.showFinishedGame(gameState);
        }
        
        // Update leaderboard
        this.updateLeaderboard();
    }
    
    showWaitingState() {
        this.elements.waitingMessage.style.display = 'block';
        this.elements.gameActive.style.display = 'none';
        this.elements.gameFinished.style.display = 'none';
        
        this.clearTimer();
    }
    
    showActiveGame(gameState) {
        this.elements.waitingMessage.style.display = 'none';
        this.elements.gameActive.style.display = 'block';
        this.elements.gameFinished.style.display = 'none';
        
        // Update round info
        if (this.elements.roundInfo) {
            this.elements.roundInfo.textContent = `Round ${gameState.current_round} of ${gameState.total_rounds}`;
        }
        
        // Update logo
        if (gameState.logo_url && this.elements.currentLogo) {
            this.elements.currentLogo.src = gameState.logo_url;
            this.elements.currentLogo.style.display = 'block';
        }
        
        // Update timer
        this.updateTimer(gameState.time_remaining);
        
        // Update guess form state
        this.updateGuessForm(gameState);
    }
    
    showFinishedGame(gameState) {
        this.elements.waitingMessage.style.display = 'none';
        this.elements.gameActive.style.display = 'none';
        this.elements.gameFinished.style.display = 'block';
        
        if (this.elements.finalScore) {
            this.elements.finalScore.textContent = gameState.team_score;
        }
        
        this.clearTimer();
    }
    
    updateTimer(timeRemaining) {
        if (this.elements.timeRemaining) {
            this.elements.timeRemaining.textContent = Math.ceil(timeRemaining);
        }
        
        // Clear existing timer
        this.clearTimer();
        
        // Start new timer if round is active
        if (timeRemaining > 0) {
            this.timerInterval = setInterval(() => {
                timeRemaining--;
                if (this.elements.timeRemaining) {
                    this.elements.timeRemaining.textContent = Math.ceil(Math.max(0, timeRemaining));
                }
                
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
    
    updateGuessForm(gameState) {
        const isRoundActive = gameState.round_active && gameState.time_remaining > 0;
        const hasGuessed = gameState.has_guessed;
        
        if (this.elements.guessInput) {
            this.elements.guessInput.disabled = !isRoundActive || hasGuessed;
        }
        
        if (this.elements.submitBtn) {
            this.elements.submitBtn.disabled = !isRoundActive || hasGuessed;
            
            if (hasGuessed) {
                this.elements.submitBtn.innerHTML = '<i class="fas fa-check me-2"></i>Guess Submitted';
                this.elements.submitBtn.classList.remove('btn-primary');
                this.elements.submitBtn.classList.add('btn-success');
            } else if (isRoundActive) {
                this.elements.submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Guess';
                this.elements.submitBtn.classList.remove('btn-success');
                this.elements.submitBtn.classList.add('btn-primary');
            } else {
                this.elements.submitBtn.innerHTML = '<i class="fas fa-clock me-2"></i>Time Up';
                this.elements.submitBtn.classList.remove('btn-primary', 'btn-success');
                this.elements.submitBtn.classList.add('btn-secondary');
            }
        }
    }
    
    async submitGuess() {
        const guess = this.elements.guessInput.value.trim();
        
        if (!guess) {
            alert('Please enter a guess');
            return;
        }
        
        try {
            // Disable form while submitting
            this.elements.guessInput.disabled = true;
            this.elements.submitBtn.disabled = true;
            this.elements.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
            
            const response = await fetch('/api/submit_guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    team_name: this.teamName,
                    guess: guess
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showGuessResult(data.is_correct, data.correct_answer);
                // Clear the input
                this.elements.guessInput.value = '';
                // Update status immediately
                this.updateStatus();
            } else {
                alert(data.error || 'Failed to submit guess');
                // Re-enable form
                this.elements.guessInput.disabled = false;
                this.elements.submitBtn.disabled = false;
                this.elements.submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Guess';
            }
            
        } catch (error) {
            console.error('Failed to submit guess:', error);
            alert('Failed to submit guess. Please try again.');
            // Re-enable form
            this.elements.guessInput.disabled = false;
            this.elements.submitBtn.disabled = false;
            this.elements.submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Guess';
        }
    }
    
    showGuessResult(isCorrect, correctAnswer) {
        if (!this.elements.guessStatus || !this.elements.guessAlert || !this.elements.guessMessage) {
            return;
        }
        
        this.elements.guessStatus.style.display = 'block';
        
        if (isCorrect) {
            this.elements.guessAlert.className = 'alert alert-success';
            this.elements.guessMessage.innerHTML = '<i class="fas fa-check-circle me-2"></i>Correct! Well done!';
        } else {
            this.elements.guessAlert.className = 'alert alert-info';
            this.elements.guessMessage.innerHTML = '<i class="fas fa-info-circle me-2"></i>Guess submitted. Wait for the round to end to see the correct answer.';
        }
        
        // Hide after 3 seconds
        setTimeout(() => {
            if (this.elements.guessStatus) {
                this.elements.guessStatus.style.display = 'none';
            }
        }, 3000);
    }
    
    async updateLeaderboard() {
        try {
            const response = await fetch('/api/admin/status');
            const data = await response.json();
            
            if (data.teams && this.elements.leaderboard) {
                // Sort teams by score
                const sortedTeams = data.teams.sort((a, b) => b.score - a.score);
                
                let html = '';
                sortedTeams.forEach((team, index) => {
                    const isCurrentTeam = team.name === this.teamName;
                    const badgeClass = index === 0 ? 'text-warning' : index === 1 ? 'text-secondary' : index === 2 ? 'text-info' : 'text-muted';
                    const rowClass = isCurrentTeam ? 'table-primary' : '';
                    
                    html += `
                        <div class="d-flex justify-content-between align-items-center py-2 px-3 mb-2 rounded ${rowClass}" 
                             style="background-color: ${isCurrentTeam ? 'rgba(13, 110, 253, 0.1)' : 'rgba(255, 255, 255, 0.05)'}">
                            <div class="d-flex align-items-center">
                                <span class="badge bg-secondary me-3">${index + 1}</span>
                                <div>
                                    <strong>${team.name}</strong>
                                    ${isCurrentTeam ? '<small class="text-primary ms-2">(Your Team)</small>' : ''}
                                    <br>
                                    <small class="text-muted">${team.members.join(', ')}</small>
                                </div>
                            </div>
                            <div class="text-end">
                                <h5 class="mb-0 ${badgeClass}">
                                    <i class="fas fa-trophy me-1"></i>
                                    ${team.score}
                                </h5>
                            </div>
                        </div>
                    `;
                });
                
                this.elements.leaderboard.innerHTML = html || '<div class="text-center text-muted">No teams registered yet</div>';
            }
            
        } catch (error) {
            console.error('Failed to update leaderboard:', error);
        }
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        this.clearTimer();
    }
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.teamDashboard) {
        window.teamDashboard.destroy();
    }
});
