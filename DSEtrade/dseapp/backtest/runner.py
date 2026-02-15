from dseapp.signals.smc_engine import SMCSignalEngine
from dseapp.trade.state_machine import TradeStateMachine

class Backtester:

    def run(self, historical_data):
        results = []

        for i in range(50, len(historical_data)):
            candles = historical_data[:i]
            engine = SMCSignalEngine(candles)
            signal = engine.generate_signal()

            if signal["signal"] == "BUY":
                entry = candles[-1]["close"]
                sl = candles[-1]["low"]
                tp = entry + (entry - sl) * 2

                trade = TradeStateMachine(entry, sl, tp)

                for c in historical_data[i:]:
                    state = trade.update(c["close"])
                    if state in ["TP_HIT", "SL_HIT"]:
                        results.append(state)
                        break

        return results
