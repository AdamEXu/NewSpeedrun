function loadLeaderboard(game) {
  const buttons = document.getElementsByClassName('tab-button');
  for (let button of buttons) {
      button.disabled = false;
  }
  document.getElementById(game).disabled = true;

  fetch(`/leaderboard?game=${game}`)
    .then(response => response.json())
    .then(data => {
        // set the game name to the url
        window.history.pushState({}, '', `?game=${game}`);
        const tbody = document.getElementById('leaderboard-body');
        tbody.innerHTML = '';
        var i = 1;
        // sort data by time, and if tied by timestamp with earlier time first
        // note that time is in HH:MM:SS.ms format, so we have to convert it to seconds
        data.sort((a, b) => {
            const timeA = a.time.split(':').reduce((acc, time) => acc * 60 + parseInt(time), 0);
            const timeB = b.time.split(':').reduce((acc, time) => acc * 60 + parseInt(time), 0);
            if (timeA === timeB) {
                return a.timestamp < b.timestamp ? -1 : 1;
            }
            return timeA - timeB;
        });
        data.forEach(run => {
            const row = document.createElement('tr');
            // currently time is in SS.ms format, convert to HH:MM:SS.ms
            const time = run.time.split('.');
            const seconds = parseInt(time[0]);
            const ms = parseInt(time[1]);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            row.innerHTML = `
                <td>${i}</td>
                <td>${run.username}</td>
                <td>${hours}:${minutes % 60}:${seconds % 60}.${ms}</td>
                <td><a href="/run?id=${run.id}">View run</a></td>
                <td>${run.timestamp}</td>
            `;
            tbody.appendChild(row);
            i++;
        });
    })
    .catch(error => console.error('Error fetching leaderboard:', error));
}

// loadLeaderboard('game1')

const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const game = urlParams.get('game');

if (game) {
  loadLeaderboard(game);
} else {
    loadLeaderboard('game1');
}