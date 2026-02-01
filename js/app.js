const { createApp, ref, onMounted, computed, reactive, watch } = Vue;

const app = createApp({
    setup() {
        // --- State ---
        const price = ref(0.00);
        const change = ref(0.00);
        const dayHigh = ref(0.00);
        const dayLow = ref(0.00);
        const volume = ref(0);
        const panicLevel = ref("CALM");
        const activeTab = ref('CONSULTANT'); // Tabs: CONSULTANT, BRAIN, PORTFOLIO

        // Data from Brain
        const bestBet = ref(null);
        const currentVerdict = ref("Initializing Connection to Brain...");
        const brainLogs = ref([]);
        const portfolio = ref({
            total_pnl: 0.00,
            win_rate: 0,
            open_trades: []
        });
        const backtestHistory = ref([]);
        const backtestStats = ref({ total_decisions: 0, strategies: [], regimes: {} });

        // --- Helpers ---
        const formatVol = (num) => {
            if (!num) return '0';
            if (num > 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num > 1000) return (num / 1000).toFixed(1) + 'K';
            return num;
        };

        const formatChange = (val) => {
            if (isNaN(val)) return '0.00%';
            return (val >= 0 ? '+' : '') + val + '%';
        };

        const getPanicColor = (level) => {
            if (level.includes("EXTREME")) return "text-red-500 animate-pulse";
            if (level.includes("HIGH")) return "text-orange-400";
            if (level.includes("LOW")) return "text-blue-400";
            return "text-green-400";
        };

        const translateIV = (iv) => {
            // Panic Meter
            if (iv > 0.80) return "EXTREME (Crash Risk)";
            if (iv > 0.50) return "HIGH (Fear)";
            if (iv > 0.30) return "NORMAL";
            return "LOW (Complacent)";
        };

        const generateLogs = (verdict, bet) => {
            // Visualize Thinking Process
            const logs = [];
            const time = new Date().toLocaleTimeString();

            logs.push({ time, msg: "⚡ Scanning Market Protocols...", color: "text-gray-500" });

            if (verdict && verdict.includes("BLOCKED")) {
                logs.push({ time, msg: "⚠️ SAFETY SHIELD ACTIVATED", color: "text-red-500 font-bold" });
                logs.push({ time, msg: verdict, color: "text-red-400" });
            } else {
                logs.push({ time, msg: "✅ Market Regime Validated", color: "text-green-500" });
                logs.push({ time, msg: `⚖️ Judge: ${verdict}`, color: "text-blue-300" });
                if (bet) {
                    logs.push({ time, msg: `🎯 Selected: ${bet.strategy_name}`, color: "text-yellow-400" });
                    logs.push({ time, msg: `📊 Confidence: ${bet.prediction.confidence}%`, color: "text-yellow-400" });
                }
            }
            return logs;
        };

        const formatDate = (timestamp) => {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        };

        // --- Data Loader ---
        const loadStrategyData = () => {
            if (window.STRATEGY_DATA) {
                const data = window.STRATEGY_DATA;

                // 1. Update Consultant (The Verdict)
                bestBet.value = data.best_bet;
                currentVerdict.value = data.judge_verdict || "Waiting for Judge...";

                // 2. Update Brain Logs
                brainLogs.value = generateLogs(currentVerdict.value, bestBet.value);

                // 3. Update Portfolio
                if (data.portfolio) {
                    portfolio.value = data.portfolio || { total_pnl: 0, win_rate: 0, total_trades: 0, open_trades: [], history: [] };
                    backtestHistory.value = data.backtest_history || [];
                    backtestStats.value = data.backtest_stats || { total_decisions: 0, strategies: [], regimes: {} };
                }

                // 4. Update Market Stats (Real Data)
                if (data.market_stats) {
                    price.value = data.market_stats.price;
                    change.value = data.market_stats.change_pct;
                    dayHigh.value = data.market_stats.day_high;
                    dayLow.value = data.market_stats.day_low;
                    volume.value = data.market_stats.volume;
                    panicLevel.value = translateIV(data.market_stats.panic_score);
                }
            }
        };

        // --- Hot Reload Logic ---
        const refreshStrategyData = () => {
            const oldScript = document.getElementById('strategy-data-script');
            if (oldScript) oldScript.remove();

            const script = document.createElement('script');
            script.id = 'strategy-data-script';
            script.src = 'js/strategy_data.js?t=' + Date.now();
            script.onload = loadStrategyData;
            document.body.appendChild(script);
        };

        onMounted(() => {
            // Initial Connect
            refreshStrategyData();

            // Poll every 5s
            setInterval(() => {
                refreshStrategyData();
            }, 5000);
        });

        return {
            activeTab,
            price, change, dayHigh, dayLow, volume, panicLevel,
            currentVerdict, bestBet, portfolio,
            backtestHistory, backtestStats,
            brainLogs,
            formatVol, formatChange, getPanicColor, formatDate
        };
    }
});

app.mount('#app');
