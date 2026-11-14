/**
 * Visualizations & Charts Module for Landslide Risk Mapper
 * Built with Chart.js
 */

const ChartsModule = (() => {
  let contributionChartInstance = null;
  let rainfallChartInstance = null;
  let riskDonutChartInstance = null;

  function initOrUpdateContributionChart(factorScores, factorContribs, weights) {
    const ctx = document.getElementById('factor-chart');
    if (!ctx) return;

    const labels = [
      `Slope (${Math.round(weights.slope * 100)}%)`,
      `Rainfall (${Math.round(weights.rainfall * 100)}%)`,
      `Terrain (${Math.round(weights.terrain * 100)}%)`
    ];

    const rawScores = [factorScores.slope, factorScores.rainfall, factorScores.terrain];
    const contribs = [factorContribs.slope, factorContribs.rainfall, factorContribs.terrain];

    if (contributionChartInstance) {
      contributionChartInstance.data.labels = labels;
      contributionChartInstance.data.datasets[0].data = rawScores;
      contributionChartInstance.data.datasets[1].data = contribs;
      contributionChartInstance.update();
      return;
    }

    contributionChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Raw Factor Score (0–100)',
            data: rawScores,
            backgroundColor: 'rgba(79, 119, 45, 0.45)',
            borderColor: '#31572c',
            borderWidth: 1.5,
            borderRadius: 6
          },
          {
            label: 'Weighted Contribution Points',
            data: contribs,
            backgroundColor: 'rgba(234, 88, 12, 0.8)',
            borderColor: '#c2410c',
            borderWidth: 1.5,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { font: { size: 11, weight: '600' } }
          },
          tooltip: {
            callbacks: {
              label: (item) => `${item.dataset.label}: ${item.raw.toFixed(1)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { font: { size: 10 } }
          },
          x: {
            ticks: { font: { size: 11 } }
          }
        }
      }
    });
  }

  function initOrUpdateRainfallChart(dates, dailyPrecip) {
    const ctx = document.getElementById('rainfall-chart');
    if (!ctx) return;

    const formattedDates = (dates || []).map(d => {
      try {
        const parts = d.split('-');
        return `${parts[1]}/${parts[2]}`;
      } catch (e) {
        return d;
      }
    });

    if (rainfallChartInstance) {
      rainfallChartInstance.data.labels = formattedDates;
      rainfallChartInstance.data.datasets[0].data = dailyPrecip;
      rainfallChartInstance.update();
      return;
    }

    rainfallChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: formattedDates,
        datasets: [
          {
            label: 'Daily Precipitation (mm)',
            data: dailyPrecip,
            backgroundColor: 'rgba(2, 132, 199, 0.7)',
            borderColor: '#0284c7',
            borderWidth: 1.5,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: { font: { size: 11, weight: '600' } }
          },
          tooltip: {
            callbacks: {
              afterBody: (context) => {
                const val = context[0].raw;
                if (val > 100) return '⚠️ Severe Flash/Debris Threshold';
                if (val > 50) return '⚠️ Heavy Monsoon Saturation';
                return 'Normal / Moderate';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Rainfall (mm)', font: { size: 11 } },
            ticks: { font: { size: 10 } }
          },
          x: {
            ticks: { font: { size: 10 } }
          }
        }
      }
    });
  }

  function initOrUpdateRiskDistributionChart(features) {
    const ctx = document.getElementById('risk-distribution-chart');
    if (!ctx) return;

    let counts = {
      "Low Risk": 0,
      "Moderate Risk": 0,
      "High Risk": 0,
      "Very High Risk": 0
    };

    if (features && features.length) {
      features.forEach(f => {
        const level = f.properties && f.properties.risk_level;
        if (counts[level] !== undefined) {
          counts[level]++;
        } else {
          counts["Moderate Risk"]++;
        }
      });
    } else {
      counts = { "Low Risk": 1, "Moderate Risk": 1, "High Risk": 1, "Very High Risk": 1 };
    }

    const dataVals = [counts["Low Risk"], counts["Moderate Risk"], counts["High Risk"], counts["Very High Risk"]];
    const total = dataVals.reduce((a, b) => a + b, 0) || 1;

    const labels = [
      `Low (${Math.round((counts["Low Risk"] / total) * 100)}%)`,
      `Moderate (${Math.round((counts["Moderate Risk"] / total) * 100)}%)`,
      `High (${Math.round((counts["High Risk"] / total) * 100)}%)`,
      `Very High (${Math.round((counts["Very High Risk"] / total) * 100)}%)`
    ];

    if (riskDonutChartInstance) {
      riskDonutChartInstance.data.labels = labels;
      riskDonutChartInstance.data.datasets[0].data = dataVals;
      riskDonutChartInstance.update();
      return;
    }

    riskDonutChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: dataVals,
          backgroundColor: [
            '#22c55e', // Low Risk Green
            '#eab308', // Moderate Risk Yellow
            '#f97316', // High Risk Orange
            '#ef4444'  // Very High Risk Red
          ],
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 12,
              font: { size: 11, weight: '600' }
            }
          },
          tooltip: {
            callbacks: {
              label: (item) => {
                const count = item.raw;
                const pct = Math.round((count / total) * 100);
                return ` ${item.label.split(' ')[0]}: ${count} cells (${pct}% of surveyed area)`;
              }
            }
          }
        },
        cutout: '65%'
      }
    });
  }

  return {
    initOrUpdateContributionChart,
    initOrUpdateRainfallChart,
    initOrUpdateRiskDistributionChart
  };
})();

window.ChartsModule = ChartsModule;

