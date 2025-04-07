document.addEventListener('DOMContentLoaded', () => {
    // Elementy interfejsu
    const startBtn = document.getElementById('start-btn');
    const nextBtn = document.getElementById('next-btn');
    const revealAllBtn = document.getElementById('reveal-all-btn');
    const switchTeamBtn = document.getElementById('switch-team-btn');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const questionElement = document.getElementById('question');
    const answersContainer = document.getElementById('answers-container');
    const answerInput = document.getElementById('answer-input');
    const team1Score = document.getElementById('team1-score');
    const team1Warnings = document.getElementById('team1-warnings');
    const team2Score = document.getElementById('team2-score');
    const team2Warnings = document.getElementById('team2-warnings');
    const currentTeamIndicator = document.getElementById('current-team');
    const team1NameDisplay = document.getElementById('team1-name-display');
    const team2NameDisplay = document.getElementById('team2-name-display');
    const teamSetup = document.getElementById('team-setup');

    let currentGameState = null;
    let gameBlocked = false;

    // Funkcja aktualizująca UI
    function updateUI(gameState) {
        currentGameState = gameState;
        
        // Sprawdź czy obie drużyny mają po 3 ostrzeżenia
        if (gameState.team1.warnings >= 3 && gameState.team2.warnings >= 3) {
            gameBlocked = true;
            answerInput.disabled = true;
            submitAnswerBtn.disabled = true;
            switchTeamBtn.disabled = true;
            revealAllBtn.disabled = false;
            
            // Automatycznie pokaż wszystkie odpowiedzi
            if (!answersContainer.querySelectorAll('.answer.revealed').length === 
                currentGameState.current_question.answers.length) {
                revealAllAnswers();
            }
        }
        
        // Aktualizacja wyników i ostrzeżeń
        team1Score.textContent = gameState.team1.score;
        team1Warnings.textContent = gameState.team1.warnings;
        team2Score.textContent = gameState.team2.score;
        team2Warnings.textContent = gameState.team2.warnings;
        
        // Aktualizacja aktualnej drużyny
        currentTeamIndicator.textContent = gameState.current_team === 1 
            ? gameState.team1.name 
            : gameState.team2.name;
        
        // Aktywacja/dezaktywacja przycisków
        startBtn.disabled = gameState.current_question !== null;
        nextBtn.disabled = gameState.current_question === null;
        revealAllBtn.disabled = gameState.current_question === null || gameBlocked;
        switchTeamBtn.disabled = gameState.current_question === null || gameBlocked;
    }

    // Rozpoczęcie gry
    async function startGame() {
        gameBlocked = false;
        answerInput.disabled = false;
        submitAnswerBtn.disabled = false;
        
        const team1Name = document.getElementById('team1-name').value.trim();
        const team2Name = document.getElementById('team2-name').value.trim();
        const startingTeam = parseInt(document.getElementById('first-team').value);

        const response = await fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                team1Name: team1Name, 
                team2Name: team2Name, 
                startingTeam: startingTeam 
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            questionElement.textContent = data.question.question_text;
            currentGameState = data.game_state;
            team1NameDisplay.textContent = team1Name;
            team2NameDisplay.textContent = team2Name;
            teamSetup.style.display = 'none';
            renderAnswers();
            updateUI(data.game_state);
        } else {
            console.error('Błąd rozpoczęcia gry:', data.error);
            alert('Nie udało się rozpocząć gry: ' + data.error);
        }
    }

    // Renderowanie odpowiedzi
    function renderAnswers() {
        answersContainer.innerHTML = '';
        
        if (currentGameState?.current_question?.answers) {
            currentGameState.current_question.answers.forEach(answer => {
                const answerDiv = document.createElement('div');
                answerDiv.classList.add('answer');
                answerDiv.dataset.answerId = answer.id;
                
                const isRevealed = currentGameState.revealed_answers.includes(answer.id);
                const isCorrect = currentGameState.correct_answers?.includes(answer.id);

                if (isRevealed || isCorrect) {
                    answerDiv.innerHTML = `${answer.answer_text} (${answer.points} pkt)`;
                    answerDiv.classList.add(isCorrect ? 'correct-answer' : 'revealed');
                    
                    // Jeśli gra zablokowana, pokaż wszystkie odpowiedzi
                    if (gameBlocked && !isRevealed && !isCorrect) {
                        answerDiv.classList.add('revealed');
                    }
                } else if (gameBlocked) {
                    // Jeśli gra zablokowana, pokaż wszystkie odpowiedzi
                    answerDiv.innerHTML = `${answer.answer_text} (${answer.points} pkt)`;
                    answerDiv.classList.add('revealed');
                } else {
                    answerDiv.textContent = '❓❓❓';
                    answerDiv.addEventListener('click', () => revealAnswer(answer.id));
                }
                
                answersContainer.appendChild(answerDiv);
            });
        }
    }

    // Sprawdzanie odpowiedzi
    async function submitAnswer() {
        if (!currentGameState?.current_question || gameBlocked) return;
        
        const answer = answerInput.value.trim().toLowerCase();
        if (!answer) return;  // Zabezpieczenie przed pustą odpowiedzią
        
        answerInput.value = '';
    
        try {
            const response = await fetch('/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    answer: answer
                    // Nie wysyłamy team, bo backend sam pobiera current_team
                })
            });
            
            const data = await response.json();
    
            if (data.success) {
                // Aktualizujemy cały stan gry z serwera
                currentGameState = data.game_state;
                updateUI(currentGameState);
                renderAnswers();
            } else {
                console.error('Błąd odpowiedzi:', data.error);
            }
        } catch (error) {
            console.error('Błąd podczas wysyłania odpowiedzi:', error);
        }
    }

    // Zmiana drużyny
    async function switchTeam() {
        if (!currentGameState || gameBlocked) return;
        
        try {
            const response = await fetch('/switch_team', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Aktualizujemy stan gry z odpowiedzi serwera
                currentGameState = data.game_state;
                
                // Resetujemy ostrzeżenia dla nowej drużyny
                if (currentGameState.current_team === 1) {
                    currentGameState.team1.warnings = 0;
                } else {
                    currentGameState.team2.warnings = 0;
                }
                
                // Aktualizacja UI
                updateUI(currentGameState);
                
                console.log('Zmieniono drużynę na:', 
                    currentGameState.current_team === 1 ? 
                    currentGameState.team1.name : 
                    currentGameState.team2.name);
            } else {
                console.error('Błąd zmiany drużyny:', data.error);
            }
        } catch (error) {
            console.error('Błąd podczas zmiany drużyny:', error);
        }
    }

    // Ujawnienie wszystkich odpowiedzi
    async function revealAllAnswers() {
        if (!currentGameState?.current_question) return;
        
        const response = await fetch('/reveal_all', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            currentGameState.revealed_answers = data.game_state.revealed_answers;
            updateUI(data.game_state);
            renderAnswers();
        } else {
            console.error('Błąd ujawniania odpowiedzi:', data.error);
        }
    }

    // Następne pytanie
    async function nextQuestion() {
        gameBlocked = false;
        answerInput.disabled = false;
        submitAnswerBtn.disabled = false;
        
        const response = await fetch('/next', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            questionElement.textContent = data.question.question_text;
            currentGameState = data.game_state;
            renderAnswers();
            updateUI(data.game_state);
        } else {
            console.error('Błąd:', data.error);
        }
    }

    // Nasłuchiwanie zdarzeń
    startBtn.addEventListener('click', startGame);
    nextBtn.addEventListener('click', nextQuestion);
    revealAllBtn.addEventListener('click', revealAllAnswers);
    switchTeamBtn.addEventListener('click', switchTeam);
    submitAnswerBtn.addEventListener('click', submitAnswer);
    
    answerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') submitAnswer();
    });
});