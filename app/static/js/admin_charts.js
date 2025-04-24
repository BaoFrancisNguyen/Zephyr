/**
 * Script pour générer les graphiques du tableau de bord administratif de Zephir Drones
 * Utilise Chart.js pour créer des visualisations interactives des données de vente
 */

// Fonction principale d'initialisation des graphiques
function initCharts(dronesData, dateData, modelData, monthlyData) {
    // S'assurer que Chart.js est chargé
    if (typeof Chart === 'undefined') {
        console.error('Chart.js n\'est pas chargé. Veuillez inclure la bibliothèque Chart.js.');
        return;
    }

    // Configuration des couleurs
    const colors = {
        primary: 'rgba(0, 86, 179, 0.7)',     // Bleu Zephir (primaire)
        primaryBorder: 'rgba(0, 86, 179, 1)',
        debutant: 'rgba(75, 192, 192, 0.7)',  // Cyan
        debutantBorder: 'rgba(75, 192, 192, 1)',
        intermediaire: 'rgba(54, 162, 235, 0.7)', // Bleu
        intermediaireBorder: 'rgba(54, 162, 235, 1)',
        expert: 'rgba(153, 102, 255, 0.7)',   // Violet
        expertBorder: 'rgba(153, 102, 255, 1)',
        revenue: 'rgba(255, 99, 132, 0.7)',   // Rouge
        revenueBorder: 'rgba(255, 99, 132, 1)',
        orders: 'rgba(255, 159, 64, 0.7)',    // Orange
        ordersBorder: 'rgba(255, 159, 64, 1)',
    };

    // 1. Graphique de répartition par niveau de drone (camembert)
    initDroneTypeChart(dronesData, colors);
    
    // 2. Graphique des modèles les plus vendus (barres)
    if (modelData) {
        initTopModelsChart(modelData, colors);
    }
    
    // 3. Graphique des ventes quotidiennes (ligne)
    if (dateData) {
        initDailySalesChart(dateData, colors);
    }
    
    // 4. Graphique du chiffre d'affaires mensuel (barres)
    if (monthlyData) {
        initMonthlyRevenueChart(monthlyData, colors);
    }
}

// Initialisation du graphique des types de drones
function initDroneTypeChart(data, colors) {
    const ctx = document.getElementById('droneTypeChart');
    if (!ctx) return;

    // Déterminer les couleurs en fonction des niveaux
    const backgroundColor = data.labels.map(label => {
        const key = label.toLowerCase();
        return colors[key] || colors.primary;
    });
    
    const borderColor = data.labels.map(label => {
        const key = label.toLowerCase();
        return colors[key + 'Border'] || colors.primaryBorder;
    });

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: data.data,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialisation du graphique des modèles les plus vendus
function initTopModelsChart(data, colors) {
    const ctx = document.getElementById('droneModelChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Nombre de ventes',
                data: data.data,
                backgroundColor: Object.values(colors).slice(0, 5),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Initialisation du graphique des ventes quotidiennes
function initDailySalesChart(data, colors) {
    const ctx = document.getElementById('dailySalesChart');
    if (!ctx) return;

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Nombre de commandes',
                    data: data.orders,
                    backgroundColor: colors.orders,
                    borderColor: colors.ordersBorder,
                    borderWidth: 2,
                    yAxisID: 'y-orders',
                    tension: 0.2
                },
                {
                    label: 'Chiffre d\'affaires (€)',
                    data: data.sales,
                    backgroundColor: colors.revenue,
                    borderColor: colors.revenueBorder,
                    borderWidth: 2,
                    yAxisID: 'y-sales',
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                'y-orders': {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Nombre de commandes'
                    },
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                },
                'y-sales': {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Chiffre d\'affaires (€)'
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });

    // Ajouter la fonctionnalité de filtrage
    document.querySelectorAll('.btn-group button[data-range]').forEach(button => {
        button.addEventListener('click', function() {
            // Mettre à jour les classes actives
            document.querySelectorAll('.btn-group button').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Filtrer les données
            const range = this.getAttribute('data-range');
            filterChartData(chart, data, range);
        });
    });
}

// Fonction pour filtrer les données du graphique
function filterChartData(chart, data, range) {
    if (range === 'all') {
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.orders;
        chart.data.datasets[1].data = data.sales;
    } else {
        const rangeNum = parseInt(range);
        chart.data.labels = data.labels.slice(-rangeNum);
        chart.data.datasets[0].data = data.orders.slice(-rangeNum);
        chart.data.datasets[1].data = data.sales.slice(-rangeNum);
    }
    chart.update();
}

// Initialisation du graphique des revenus mensuels
function initMonthlyRevenueChart(data, colors) {
    const ctx = document.getElementById('monthlyRevenueChart');
    if (!ctx) return;

    // Formatter les dates pour l'affichage
    const formattedLabels = data.labels.map(month => {
        try {
            const [year, monthNum] = month.split('-');
            const date = new Date(parseInt(year), parseInt(monthNum) - 1);
            return date.toLocaleDateString('fr', { month: 'long', year: 'numeric' });
        } catch(e) {
            return month; // Fallback en cas d'erreur
        }
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: formattedLabels,
            datasets: [{
                label: 'Chiffre d\'affaires (€)',
                data: data.sales,
                backgroundColor: colors.revenue,
                borderColor: colors.revenueBorder,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Chiffre d\'affaires (€)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Mois'
                    }
                }
            }
        }
    });
}

// Détecter les erreurs de données
function checkDataValidity(data) {
    if (!data) {
        console.error('Données manquantes pour les graphiques');
        return false;
    }
    
    if (!Array.isArray(data.labels) || !Array.isArray(data.data)) {
        console.error('Format de données incorrect. Structure attendue: {labels: [...], data: [...]}');
        return false;
    }
    
    if (data.labels.length !== data.data.length) {
        console.error('Incohérence: le nombre de labels ne correspond pas au nombre de données');
        return false;
    }
    
    return true;
}

// Exporter les fonctions pour une utilisation directe dans les templates
window.ZephirCharts = {
    init: initCharts,
    droneTypes: initDroneTypeChart,
    topModels: initTopModelsChart,
    dailySales: initDailySalesChart,
    monthlyRevenue: initMonthlyRevenueChart
};