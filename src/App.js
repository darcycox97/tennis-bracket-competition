import { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2'
import './App.css';

function calculateScores(data) {
  let scores = []
  data.teams.forEach(t => {
    let s = {
      name: t.name,
      score: 0
    }
    data.matches.forEach(m => {
      if (t.players.includes(m.winner)) {
        const incr = m.tags.includes("default_win") ? 0.5 : 1
        s.score = s.score + incr
      }
    })

    scores.push(s)
  })

  return scores
}

function chartConfig(tourneyName, scores) {
  const chartData = {
    labels: scores.map(t => t.name),
    datasets: [
      {
        label: '# of wins',
        data: scores.map(t => t.score),
        backgroundColor: [
          'rgba(255, 206, 86, 0.2)',
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
        ],
        borderColor: [
          'rgba(255, 206, 86, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
        ],
      },
    ],
  };

  const chartOptions = {
    maintainAspectRatio: false,
    barPercentage: 0.5,
    maxBarThickness: 40,
    indexAxis: 'x',
    // Elements options apply to all of the options unless overridden in a dataset
    // In this case, we are setting the border of each horizontal bar to be 2px wide
    elements: {
      bar: {
        borderWidth: 2
      },
    },
    responsive: true,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: tourneyName,
        fullSize: true,
        font: {
          size: 30
        },
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          font: {
            size: 20
          }
        }
      },
      y: {
        ticks: {
          font: {
            size: 12
          }
        }
      },
    }
  };

  return {
    chartData,
    chartOptions
  }
}

async function fetchData() {
  if (process.env.NODE_ENV === "development") {
    const sampleData = await fetch("./tournament.json")
    console.log(sampleData)
    let data = await sampleData.json()
    return data
  }

  return await (await fetch("https://novakfanclub.xyz/api/tennis-tournament-results?tournamentName=US+Open+2021")).json()
}

function renderTeam(team) {
  return (
    <div className="team-list">
      <h3>{team.name}</h3>
      <ul>
        {team.players.map(p => <li>{p}</li>)}
      </ul>
    </div>
  )
}

function App() {

  const [state, setState] = useState(null);

  useEffect(() => {
    const getData = async () => {
      const tourneyData = await fetchData()
      const scores = calculateScores(tourneyData)
      const { chartData, chartOptions } = chartConfig(tourneyData.tournament_name, scores)
      setState({
        tourneyData,
        chartData,
        chartOptions
      })
    }
    if (!state) {
      getData()
    }
  });

  return (
    <div className="App">
      <header className="App-header">
        {state && <Bar data={state.chartData} options={state.chartOptions} />}
        {state && state.tourneyData.teams.map(renderTeam)}
      </header>
    </div>
  );
}

export default App;
