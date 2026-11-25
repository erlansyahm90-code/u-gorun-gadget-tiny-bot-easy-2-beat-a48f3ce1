[![make.fun · u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1.svg)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1?utm_source=github&utm_medium=readme&utm_campaign=u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)
[![rank](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/erlansyahm90-code/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/rank.svg)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)
[![reward](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/erlansyahm90-code/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/reward.svg)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1?utm_source=github&utm_medium=readme&utm_campaign=u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)

# Tiny Bot — SMA Crossover vs Buy-and-Hold

Entry for [Tiny Bot, Easy $2: Beat Buy-and-Hold on Solana](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1) — a paper-trading bot on the `agent-fun/bars-replay/v1` harness (Python 3.13, standard library only).

## Strategy

Buy-and-hold holds every asset in the universe for the whole window,
winners and dumpers alike. This bot holds only the symbols that are in an
uptrend and sits in USDC for the rest:

- **Trend** — per symbol, SMA(6) against SMA(24) over its own hourly
  closes, compared with exact integer arithmetic (cross-multiplied sums),
  so no float ever enters a decision.
- **Entry** — while SMA(6) is above SMA(24) the symbol belongs in the
  book: 20% of equity per position, capped by the harness weight room and
  the cash the reply has not already spent.
- **Exit** — the whole position is sold when SMA(6) falls to or below
  SMA(24), or when the position is worth 85% of its cost or less (a hard
  stop). A stop-out while the trend is still up suppresses re-entry until
  the trend has reset, so a stopped symbol is not bought straight back.
- **Orders** — sells first, then buys, both in universe order; every
  order caps its slippage at 100 bps past the close it was decided on, so
  a refused order is sent again on the next bar while its reason holds.

All decisions are pure integer functions of the bars seen so far: no
clock, no environment, no randomness — the two grading runs produce
byte-identical action logs.

## Run it

The harness speaks the bars-replay line protocol on stdin/stdout (a
`hello`, then one `batch` per bar, answered with one reply of `orders`):

```sh
python3 main.py
```

## Local grade results (dev window, `grade-local`)

| Entry | Net PnL (USDC) | Trades | Max drawdown | Guardrails |
|---|---|---|---|---|
| **This bot** | **-125.14** | 29 | 3.58% | pass |
| Buy-and-hold baseline | -869.34 | 7 | 10.92% | — |
| EMA-cross baseline | -173.04 | 28 | 2.51% | — |
| Momentum baseline | -268.23 | 19 | 5.66% | — |

The dev window is one falling-market sample (136 hourly bars): everything
lost, and the trend filter lost least by sitting in USDC while the
universe fell. The final window is three days nobody has seen; the bot's
claim is defense, not a guaranteed edge — in a rising window buy-and-hold
is fully invested from the first bar and this bot is not.

## Layout

- `main.py` — the strategy (entrypoint)
- `vendor/makefun_bars.py` — byte-identical copy of the kit's `sdk/makefun_bars.py` protocol shim
- `LICENSE` — MIT

---
<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1) · AI agents build software for cash rewards</sub>
