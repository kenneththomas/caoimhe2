fetch('/point-balance-data')
.then(response => response.json())
.then(data => {
    const ctx = document.getElementById('pointBalanceChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Point Balance',
                data: data.map(item => ({ x: item.date, y: item.points })),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Points'
                    },
                    beginAtZero: false
                }
            }
        }
    });
});