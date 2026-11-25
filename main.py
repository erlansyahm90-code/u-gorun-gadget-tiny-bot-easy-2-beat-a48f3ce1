"""Tiny Bot: a moving-average crossover for the agent-fun/bars-replay/v1 harness.

Strategy, per symbol over its own hourly closes:

  - Trend: SMA(6) against SMA(24), compared with exact integer arithmetic
    (sum of the last 6 closes times 24 against the sum of the last 24 closes
    times 6), so no float ever enters a decision and the two grading runs
    produce byte-identical orders.
  - Entry: while SMA(6) is above SMA(24) the symbol belongs in the book. The
    first batch that can trade on (after any warm-up) buys every symbol
    already in an uptrend; later batches buy a symbol when its trend is up
    and it is not held.
  - Exit: the whole position is sold on the first batch whose close puts
    SMA(6) at or below SMA(24), or when the position is worth 85% of its
    cost or less (a hard stop). A stop-out while the trend is still up
    suppresses re-entry until the trend has reset (SMA(6) below SMA(24)
    once), so a stopped symbol is not bought straight back.
  - Size: 20% of equity per position, capped by the harness weight room
    (caps.max_weight_bps of equity less what the symbol already holds) and
    by the cash this reply has not already spent. A buy below
    fees.min_notional_quote_units is skipped.
  - Orders: sells first, then buys, both in the hello universe order, at
    most caps.max_orders_per_bar in a reply; every order caps its slippage
    at 100 bps past the close it was decided on, so a refused order is
    simply sent again on the next bar while its reason still holds.

The bot reads the hello for its caps and fees, folds every batch's bars
into the close history (warm-up batches included, though no order decided
on one is ever sent), and answers each batch with its orders. It never
reads the clock, the environment or a random source.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

FAST_BARS = 6
SLOW_BARS = 24
TARGET_BPS = 2000  # 20% of equity per position
STOP_NUM = 85  # sell when a position is worth STOP_NUM / STOP_DEN of its cost
STOP_DEN = 100
MAX_SLIPPAGE_BPS = 100

closes = {}  # symbol -> its closes so far, oldest first
stopped = set()  # symbols stopped out while their trend was up: no re-entry until the trend resets


def trend(symbol):
    """1 when SMA(FAST_BARS) is above SMA(SLOW_BARS), -1 when below, 0 when equal or not enough bars yet."""
    history = closes.get(symbol)
    if history is None or len(history) < SLOW_BARS:
        return None
    fast = sum(history[-FAST_BARS:])
    slow = sum(history[-SLOW_BARS:])
    gap = fast * SLOW_BARS - slow * FAST_BARS
    if gap > 0:
        return 1
    if gap < 0:
        return -1
    return 0


def on_batch(state, batch):
    fresh = set()
    for bar in batch["bars"]:
        closes.setdefault(bar["symbol"], []).append(int(bar["c"]))
        fresh.add(bar["symbol"])
    if state.warming_up:
        return []

    caps = state.hello["caps"]
    min_notional = int(state.hello["fees"]["min_notional_quote_units"])
    orders = []

    # A downtrend close on any fresh bar resets a stopped symbol's suppression,
    # held or not: from here it may be bought again on its next uptrend.
    for info in state.hello["symbols"]:
        symbol = info["symbol"]
        if symbol in fresh and symbol in stopped:
            direction = trend(symbol)
            if direction is not None and direction < 0:
                stopped.discard(symbol)

    # Sells first, in universe order: a downtrend close or the hard stop ends the position.
    for info in state.hello["symbols"]:
        symbol = info["symbol"]
        if symbol not in fresh:
            continue
        held = state.positions.get(symbol)
        if held is None:
            continue
        direction = trend(symbol)
        stop_hit = state.value(symbol, held.qty) * STOP_DEN <= held.cost * STOP_NUM
        if (direction is not None and direction <= 0) or stop_hit:
            orders.append({"side": "sell", "symbol": symbol, "qty": held.qty, "max_slippage_bps": MAX_SLIPPAGE_BPS})
            if stop_hit and direction is not None and direction > 0:
                stopped.add(symbol)

    # Then buys: every unheld symbol in an uptrend, 20% of equity each, while slots and cash last.
    cash = state.cash
    slots = caps["max_open_positions"] - len(state.positions)
    for info in state.hello["symbols"]:
        symbol = info["symbol"]
        if len(orders) >= caps["max_orders_per_bar"] or slots <= 0:
            break
        if symbol not in fresh or symbol in state.positions or symbol in stopped:
            continue
        if trend(symbol) != 1:
            continue
        amount = state.equity * TARGET_BPS // 10000
        room = state.weight_room(symbol)
        if room < amount:
            amount = room
        if cash < amount:
            amount = cash
        if amount < min_notional:
            continue
        orders.append({"side": "buy", "symbol": symbol, "notional_quote_units": amount, "max_slippage_bps": MAX_SLIPPAGE_BPS})
        cash -= amount
        slots -= 1
    return orders


makefun_bars.run(on_batch)
