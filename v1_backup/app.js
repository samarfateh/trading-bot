// app.js

class App {
    constructor() {
        this.service = new StockDataService();
        this.watchlist = ['AAPL', 'VOO', 'MSFT', 'TSLA', 'GOOGL'];
        this.container = document.getElementById('watchlist-container');

        // Check for API Key
        const key = localStorage.getItem('stock_api_key');
        if (key) {
            this.service.useLive = true;
            console.log("Live mode enabled");
        }
    }

    async init() {
        this.setupSettingsEvents();
        await this.renderWatchlist();
    }

    setupSettingsEvents() {
        const modal = document.getElementById('settings-modal');
        const btn = document.getElementById('settings-btn');
        const close = document.getElementById('close-modal');
        const save = document.getElementById('save-api-key');
        const input = document.getElementById('api-key-input');

        btn.onclick = () => {
            modal.classList.remove('hidden');
            input.value = localStorage.getItem('stock_api_key') || '';
        };

        close.onclick = () => modal.classList.add('hidden');

        save.onclick = () => {
            const val = input.value.trim();
            if (val) {
                localStorage.setItem('stock_api_key', val);
                alert("Key saved! Reloading...");
                location.reload();
            }
        };
    }

    async renderWatchlist() {
        this.container.innerHTML = ''; // Clear loading state

        const stocks = await this.service.getStocks(this.watchlist);

        stocks.forEach(stock => {
            const card = this.createStockCard(stock);
            this.container.appendChild(card);

            // Render Chart if history exists
            if (stock.history && stock.history.length > 0) {
                this.renderChart(stock.symbol, stock.history, stock.guidance.rating);
            }
        });
    }

    renderChart(symbol, data, rating) {
        const canvas = document.getElementById(`chart-${symbol}`);
        if (!canvas) return;

        // Color based on rating
        let color = '#64748b'; // Neutral
        if (rating === 'Safe') color = '#10b981';
        if (rating === 'Avoid') color = '#ef4444';
        if (rating === 'Watch') color = '#f59e0b';

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: Array(data.length).fill(''),
                datasets: [{
                    data: data,
                    borderColor: color,
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });
    }

    createStockCard(stock) {
        const el = document.createElement('div');
        el.className = 'stock-card';

        // Determine badge class
        let badgeClass = 'caution';
        if (stock.guidance.rating === 'Safe') badgeClass = 'safe';
        if (stock.guidance.rating === 'Avoid') badgeClass = 'avoid';

        el.innerHTML = `
            <div class="stock-info">
                <h4>${stock.symbol}</h4>
                <span class="stock-name">${stock.name}</span>
            </div>
            <div class="stock-chart-placeholder">
                <canvas id="chart-${stock.symbol}" width="100" height="40"></canvas>
            </div>
            <div class="stock-price">
                <span class="price-current">$${stock.price.toFixed(2)}</span>
                <span class="badge ${badgeClass}">${stock.guidance.rating}</span>
            </div>
        `;
        return el;
    }
}

// Initialize App when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
