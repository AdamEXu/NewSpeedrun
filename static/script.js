function loadLeaderboard(game) {
  //undisable all butons
  const buttons = document.getElementsByClassName('tab-button');
  for (let button of buttons) {
      button.disabled = false;
  }
  document.getElementById(game).disabled = true;

  fetch(`/leaderboard?game=${game}`)
      .then(response => response.json())
      .then(data => {
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
              row.innerHTML = `
                  <td>${i}</td>
                  <td>${run.username}</td>
                  <td>${run.time}</td>
                  <td><a href="/run?id=${run.id}">View run</a></td>
                  <td>${run.timestamp}</td>
              `;
              tbody.appendChild(row);
              i++;
          });
      })
      .catch(error => console.error('Error fetching leaderboard:', error));
}

loadLeaderboard('game1')