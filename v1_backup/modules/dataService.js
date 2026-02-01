// modules/dataService.js

class StockDataService {
    constructor() {
        this.useLive = false; // Toggle this later via UI to switch to Live
    }

    async getStocks(symbols) {
        if (this.useLive) {
            return this.fetchLive(symbols);
        }
        return this.fetchMock(symbols);
    }

    // --- MOCK ADAPTER ---
    async fetchMock(symbols) {
        // Simulate network delay for realism
        await new Promise(r => setTimeout(r, 600));

        return symbols.map(sym => {
            // Randomize slightly for demo feel
            const isSafe = Math.random() > 0.3;
            const price = Math.random() * 200 + 50;

            // Generate Mock History (30 days)
            const history = [];
            let currentPrice = price;
            for (let i = 0; i < 30; i++) {
                history.unshift(currentPrice);
                currentPrice = currentPrice * (1 + (Math.random() * 0.04 - 0.02)); // +/- 2% max daily move
            }

            return {
                symbol: sym,
                name: this.getName(sym),
                price: price,
                longTermAvg: price * 0.95,
                guidance: {
                    rating: isSafe ? 'Safe' : (Math.random() > 0.5 ? 'Watch' : 'Avoid'),
                    action: isSafe ? 'Good to hold' : 'Wait for dip'
                },
                history: history
            };
        });
    }

    // --- LIVE ADAPTER ---
    async fetchLive(symbols) {
        const apiKey = localStorage.getItem('stock_api_key');
        if (!apiKey) {
            console.warn("No API key found. Reverting to Mock.");
            return this.fetchMock(symbols);
        }

        const promises = symbols.map(async (sym) => {
            try {
                // Fetch Quote
                const res = await fetch(`https://finnhub.io/api/v1/quote?symbol=${sym}&token=${apiKey}`);
                const data = await res.json();

                // Finnhub Quote: c = current, pc = previous close
                const price = data.c;
                const prevClose = data.pc;

                // Simple trend derivation
                const isUp = price >= prevClose;

                return {
                    symbol: sym,
                    name: this.getName(sym),
                    price: price,
                    longTermAvg: prevClose, // Using prevClose as proxy for simple demo
                    guidance: {
                        rating: isUp ? 'Safe' : 'Watch',
                        action: isUp ? 'Trend is Positive' : 'Price is Pulling Back'
                    },
                    history: [] // Chart data would require a separate 'candle' call
                };
            } catch (err) {
                console.error("Fetch error for", sym, err);
                // Fallback to mock for this specific symbol if error
                const mock = await this.fetchMock([sym]);
                return mock[0];
            }
        });

        return Promise.all(promises);
    }

    getName(sym) {
        const map = {
            'AAPL': 'Apple Inc.',
            'VOO': 'Vanguard S&P 500',
            'MSFT': 'Microsoft Corp.',
            'TSLA': 'Tesla Inc.',
            'GOOGL': 'Alphabet Inc.'
        };
        return map[sym] || 'Unknown Company';
    }
}
