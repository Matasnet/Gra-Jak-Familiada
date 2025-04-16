function fetchGameState() {
    fetch('/api/game_state')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (typeof updateGameState === 'function') {
                updateGameState(data);
            }
        })
        .catch(error => {
            console.error('Error fetching game state:', error);
            // Retry after 1 second if there's an error
            setTimeout(fetchGameState, 1000);
        });
}

// Initialize the game state when the page loads
document.addEventListener('DOMContentLoaded', function() {
    fetchGameState();
});