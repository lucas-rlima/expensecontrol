// Apenas pra conferir se os dados chegaram certinhos:
console.log('Dias:', dias);
console.log('Valores:', valores);



const ctx = document.getElementById('grafico').getContext('2d');

Chart.register(ChartDataLabels);
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: dias,
        datasets: [{
            label: 'Gastos',
            data: valores,
            backgroundColor: 'rgba(75, 192, 192, 0.7)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
            barThickness: 15 // ?? controla a espessura das barras
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                font: {
                    size: 18
                }
            },
            datalabels: {
                display: true,  // Esta linha garante que os valores sejam mostrados
                color: 'black',  // Cor do texto
                font: {
                    weight: 'bold',  // Peso da fonte
                    size: 14  // Tamanho da fonte
                },
                formatter: function(value) {
                    return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }); // Formatação do valor
                },
                anchor: 'end',  // Posiciona o valor no final da barra
                align: 'top',  // Alinha o texto no topo da barra
        },
            legend: {
                display: false
            },
        },
        scales: {
            x: {
                ticks: {
                    autoSkip: false,
                    maxRotation: 45,
                    minRotation: 30
                },
                grid: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Dia',
                }
            },
            y: {
                beginAtZero: true,
                max: maxY,
                ticks: {
                    stepSize: 250,
                    callback: function(value) {
                        return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                    }
                },
                title: {
                    display: true,
                }
            }
        }
    },
});
