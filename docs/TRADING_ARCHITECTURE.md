# AI Trading System Architecture

## Executive Summary

This document describes a production-grade, self-learning AI trading system designed as a "living lab" - always trading, always measuring, always updating. The system implements volatility-aware position sizing, multi-horizon alpha models, and continuous model improvement through online learning.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI TRADING SYSTEM - LIVING LAB                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MONITORING LAYER                             │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │  │Dashboard │ │ Alerts   │ │Model Perf│ │Risk Dash │ │Drift Det │  │    │
│  │  │ (Grafana)│ │(PagerDuty│ │ Tracker  │ │  Board   │ │  ector   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │                     LEARNING LOOP │                                  │    │
│  │  ┌──────────────────────────────┴────────────────────────────────┐  │    │
│  │  │                   ONLINE LEARNING ENGINE                       │  │    │
│  │  │  • Shadow Trading  • A/B Testing  • Model Promotion/Demotion  │  │    │
│  │  │  • Incremental Updates  • Walk-Forward Validation              │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │                    EXECUTION LAYER │                                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────┴───┐ ┌──────────┐ ┌──────────┐  │    │
│  │  │ Smart    │ │ TWAP/    │ │ Slippage │ │ Order    │ │ Fill     │  │    │
│  │  │ Router   │ │ VWAP     │ │ Model    │ │ Manager  │ │ Tracker  │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │                RISK & PORTFOLIO LAYER │                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │  │Position  │ │ Vol      │ │ Max DD   │ │Correlation│ │ Kill     │  │    │
│  │  │ Sizer    │ │ Target   │ │ Limiter  │ │  Caps    │ │ Switch   │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │              POLICY / STRATEGY LAYER │ (THE AI BRAIN)                │    │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │    │
│  │  │ MICROSTRUCTURE  │ │ INTRADAY        │ │ SWING/POSITION  │        │    │
│  │  │ MODEL           │ │ DIRECTIONAL     │ │ MODEL           │        │    │
│  │  │ (seconds-mins)  │ │ (mins-hours)    │ │ (days-weeks)    │        │    │
│  │  │                 │ │                 │ │                 │        │    │
│  │  │ • Execution RL  │ │ • Return Pred   │ │ • Trend/MR      │        │    │
│  │  │ • Spread Capture│ │ • Hit Prob      │ │ • Factor Exp    │        │    │
│  │  │ • Queue Pos     │ │ • Regime-aware  │ │ • Cross-sect    │        │    │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘        │    │
│  │          │                   │                   │                  │    │
│  │          └───────────────────┼───────────────────┘                  │    │
│  │                              ▼                                      │    │
│  │                    ┌─────────────────┐                              │    │
│  │                    │  REGIME-AWARE   │                              │    │
│  │                    │  MODEL SELECTOR │                              │    │
│  │                    │  (Multi-Armed   │                              │    │
│  │                    │   Bandit)       │                              │    │
│  │                    └─────────────────┘                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │              FEATURE & SIGNAL LAYER │                                │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│  │  │ Price    │ │ Volume   │ │ Regime   │ │ Cross-   │ │ Factor   │  │    │
│  │  │ Features │ │ Features │ │ Labels   │ │ Sectional│ │ Exposures│  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    ▲                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐    │
│  │                     DATA LAYER   │                                   │    │
│  │  ┌────────────────────────────────┐ ┌─────────────────────────────┐ │    │
│  │  │          HOT STORAGE           │ │       COLD STORAGE          │ │    │
│  │  │  ┌──────┐ ┌──────┐ ┌──────┐  │ │ ┌──────┐ ┌──────┐ ┌──────┐ │ │    │
│  │  │  │Redis │ │Kafka │ │In-Mem│  │ │ │TimeSc│ │Parquet│ │S3/GCS│ │ │    │
│  │  │  │Streams││Streams││ Store │  │ │ │aleDB │ │  DW   │ │ Lake │ │ │    │
│  │  │  └──────┘ └──────┘ └──────┘  │ │ └──────┘ └──────┘ └──────┘ │ │    │
│  │  └────────────────────────────────┘ └─────────────────────────────┘ │    │
│  │                       ▲                          ▲                   │    │
│  │  ┌────────────────────┴──────────────────────────┴────────────────┐ │    │
│  │  │                    DATA INGESTION                               │ │    │
│  │  │  • Market Data (Tick/OHLCV/L2)  • Corp Actions  • Alt Data     │ │    │
│  │  │  • Survivorship-Bias-Free       • Point-in-Time  • Adjusted    │ │    │
│  │  └────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Language** | Python 3.11+ | Primary development |
| **Async Runtime** | asyncio + uvloop | High-performance async I/O |
| **API Framework** | FastAPI | REST/WebSocket endpoints |
| **Type Safety** | Pydantic v2 | Data validation & serialization |

### 2.2 Data Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Message Queue** | Apache Kafka | Event streaming, market data distribution |
| **Hot Cache** | Redis 7+ (Cluster) | Real-time features, session state |
| **Time-Series DB** | TimescaleDB / QuestDB | OHLCV, tick data, metrics |
| **Data Warehouse** | DuckDB / ClickHouse | Analytical queries, backtesting |
| **Object Storage** | S3 / GCS + Parquet | Historical data, model artifacts |

### 2.3 ML/AI Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Feature Store** | Feast / Custom | Point-in-time feature serving |
| **ML Training** | PyTorch / XGBoost / LightGBM | Model development |
| **RL Framework** | Stable-Baselines3 / RLlib | Reinforcement learning |
| **Experiment Tracking** | MLflow / W&B | Model versioning, metrics |
| **Model Serving** | FastAPI + ONNX / TorchServe | Low-latency inference |

### 2.4 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Kubernetes / Docker Compose | Container orchestration |
| **Monitoring** | Prometheus + Grafana | Metrics & visualization |
| **Logging** | ELK Stack / Loki | Centralized logging |
| **Alerting** | PagerDuty / OpsGenie | Incident management |
| **CI/CD** | GitHub Actions | Automated testing & deployment |

---

## 3. Data Flow Architecture

```
                                    ┌─────────────────────┐
                                    │   EXCHANGE APIs     │
                                    │  (Binance, Coinbase,│
                                    │   Interactive, etc) │
                                    └──────────┬──────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION LAYER                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │ WebSocket       │    │ REST Poller     │    │ FIX Gateway     │      │
│  │ Connector       │    │ (OHLCV, Funding)│    │ (Institutional) │      │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘      │
│           │                      │                      │                │
│           └──────────────────────┼──────────────────────┘                │
│                                  ▼                                       │
│                    ┌─────────────────────────┐                           │
│                    │    NORMALIZER           │                           │
│                    │  • Timestamp alignment  │                           │
│                    │  • Symbol mapping       │                           │
│                    │  • Data validation      │                           │
│                    └────────────┬────────────┘                           │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │     KAFKA CLUSTER       │
                    │  ┌──────────────────┐   │
                    │  │ market.ticks     │   │
                    │  │ market.ohlcv     │   │
                    │  │ market.orderbook │   │
                    │  │ signals.alpha    │   │
                    │  │ orders.new       │   │
                    │  │ orders.filled    │   │
                    │  │ risk.events      │   │
                    │  └──────────────────┘   │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FEATURE ENGINE │    │  COLD STORAGE   │    │  MONITORING     │
│                 │    │                 │    │                 │
│ • Rolling stats │    │ • TimescaleDB   │    │ • Prometheus    │
│ • Regime detect │    │ • Parquet files │    │ • Grafana       │
│ • Factor calc   │    │ • Model artifacts│   │ • Alert rules   │
│                 │    │                 │    │                 │
│    ┌───┐        │    └─────────────────┘    └─────────────────┘
│    │Redis       │
│    │Cache       │
│    └───┘        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ALPHA MODELS                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Momentum    │  │ Mean-Rev    │  │ Volatility  │              │
│  │ Signal      │  │ Signal      │  │ Breakout    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│                 ┌─────────────────┐                              │
│                 │ SIGNAL ENSEMBLE │                              │
│                 │ (Vol-weighted)  │                              │
│                 └────────┬────────┘                              │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │         RISK LAYER                   │
         │  • Position Sizing (Vol-Target)     │
         │  • Drawdown Limits                  │
         │  • Correlation Caps                 │
         │  • Kill Switch                      │
         └────────────────┬────────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────────┐
         │        EXECUTION ENGINE             │
         │  • TWAP/VWAP Slicing               │
         │  • Smart Order Routing             │
         │  • Partial Fill Handling           │
         └────────────────┬────────────────────┘
                          │
                          ▼
                    ┌───────────┐
                    │ EXCHANGE  │
                    └───────────┘
```

---

## 4. Alpha Model Design

### 4.1 Momentum-Based Alpha Model

**Objective**: Capture trending price movements by predicting the probability of continuation.

#### Mathematical Formulation

**Signal Generation:**

$$\text{momentum}_t = \frac{P_t - P_{t-n}}{P_{t-n}} \cdot \frac{1}{\sigma_t}$$

Where:
- $P_t$ = Current price
- $P_{t-n}$ = Price n periods ago
- $\sigma_t$ = Realized volatility (rolling std of returns)

**Volatility-Adjusted Momentum (VAM):**

$$\text{VAM}_t = \frac{\sum_{i=1}^{k} w_i \cdot r_{t-i}}{\sigma_{t,k}}$$

Where:
- $r_{t-i}$ = Log return at time $t-i$
- $w_i$ = Exponential decay weights: $w_i = \frac{e^{-\lambda i}}{\sum_{j=1}^{k} e^{-\lambda j}}$
- $\sigma_{t,k}$ = Rolling volatility over lookback $k$

**Trend Strength Filter:**

$$\text{ADX}_t = \frac{\text{EMA}_{14}(|+DI_t - -DI_t|)}{\text{EMA}_{14}(+DI_t + -DI_t)} \times 100$$

Only take momentum signals when $\text{ADX}_t > 25$.

**Composite Alpha:**

$$\alpha^{\text{mom}}_t = \text{sign}(\text{VAM}_t) \cdot \min(|\text{VAM}_t|, 3) \cdot \mathbb{1}_{\text{ADX}_t > 25}$$

---

### 4.2 Mean-Reversion Alpha Model

**Objective**: Exploit temporary price dislocations from fair value.

**Z-Score Signal:**

$$z_t = \frac{P_t - \mu_{t,n}}{\sigma_{t,n}}$$

Where:
- $\mu_{t,n}$ = Rolling mean price over $n$ periods
- $\sigma_{t,n}$ = Rolling standard deviation

**Bollinger Band Deviation:**

$$\text{BB}_t = \frac{P_t - \text{SMA}_{20}(P)}{2 \cdot \sigma_{20}(P)}$$

**Hurst Exponent Filter:**

Only enable mean-reversion when Hurst < 0.5 (mean-reverting regime):

$$H = \frac{\log(R/S)}{\log(n)}$$

**Composite Alpha:**

$$\alpha^{\text{mr}}_t = -\text{sign}(z_t) \cdot \min(|z_t|, 2.5) \cdot \mathbb{1}_{H < 0.5}$$

---

### 4.3 Volatility Regime Model

**Objective**: Adapt strategy behavior based on current volatility regime.

**Regime Classification:**

$$\text{Regime}_t = \begin{cases} 
\text{LOW\_VOL} & \text{if } \sigma_t < \mu_\sigma - 0.5\sigma_\sigma \\
\text{NORMAL} & \text{if } |\sigma_t - \mu_\sigma| \leq 0.5\sigma_\sigma \\
\text{HIGH\_VOL} & \text{if } \sigma_t > \mu_\sigma + 0.5\sigma_\sigma
\end{cases}$$

**GARCH(1,1) Volatility Forecast:**

$$\sigma^2_{t+1} = \omega + \alpha \cdot r_t^2 + \beta \cdot \sigma_t^2$$

---

## 5. Risk-Aware Position Sizing

### 5.1 Volatility Targeting Framework

**Core Principle**: Maintain constant risk exposure regardless of asset volatility.

**Position Size Formula:**

$$w_t = \frac{\sigma_{\text{target}}}{\sigma_t^{\text{asset}}} \cdot \frac{\text{Risk Budget}}{\text{NAV}_t}$$

Where:
- $\sigma_{\text{target}}$ = Target annualized volatility (e.g., 15%)
- $\sigma_t^{\text{asset}}$ = Current asset annualized volatility
- Risk Budget = Capital allocated to this strategy

**Annualized Volatility Calculation:**

$$\sigma_{\text{annual}} = \sigma_{\text{daily}} \cdot \sqrt{252}$$

**Example:**

If:
- $\sigma_{\text{target}} = 0.15$ (15% annual vol target)
- $\sigma_t^{\text{asset}} = 0.30$ (30% annual realized vol)
- Risk Budget = \$100,000

Then:
$$w_t = \frac{0.15}{0.30} = 0.5$$

Position size = 0.5 × \$100,000 = \$50,000 notional

---

### 5.2 Kelly Criterion with Fractional Sizing

**Full Kelly:**

$$f^* = \frac{p \cdot b - q}{b} = \frac{\mu}{\sigma^2}$$

Where:
- $p$ = Win probability
- $q = 1 - p$ = Loss probability
- $b$ = Win/loss ratio
- $\mu$ = Expected return
- $\sigma^2$ = Variance of returns

**Half-Kelly (Practical):**

$$f_{\text{practical}} = 0.5 \cdot f^*$$

**Constrained Kelly:**

$$f_{\text{final}} = \min\left(f_{\text{practical}}, f_{\text{max}}\right) \cdot \mathbb{1}_{\text{Sharpe} > \text{threshold}}$$

---

### 5.3 Multi-Strategy Portfolio Optimization

**Combined Position Size:**

$$\mathbf{w} = \frac{\sigma_{\text{target}}}{\sqrt{\mathbf{w}^T \Sigma \mathbf{w}}} \cdot \frac{\Sigma^{-1} \boldsymbol{\mu}}{\mathbf{1}^T \Sigma^{-1} \boldsymbol{\mu}}$$

Where:
- $\Sigma$ = Covariance matrix of strategy returns
- $\boldsymbol{\mu}$ = Expected returns vector

---

## 6. Pseudo-Code Implementation

### 6.1 Main Trading Loop

```python
async def trading_loop():
    """Main trading loop - the living lab heartbeat."""
    
    while market_is_open():
        # 1. Fetch latest market data
        market_data = await data_layer.get_latest()
        
        # 2. Calculate features
        features = feature_engine.compute(market_data)
        
        # 3. Detect current regime
        regime = regime_detector.classify(features)
        
        # 4. Generate alpha signals
        alpha_signals = {}
        for model in active_models[regime]:
            signal = model.predict(features)
            alpha_signals[model.name] = signal
        
        # 5. Ensemble signals (volatility-weighted)
        combined_signal = ensemble.combine(
            signals=alpha_signals,
            weights=model_selector.get_weights(regime)
        )
        
        # 6. Apply risk constraints
        target_position = risk_manager.size_position(
            signal=combined_signal,
            current_vol=features['realized_vol'],
            target_vol=config.TARGET_VOL,
            current_positions=portfolio.positions,
            max_drawdown=config.MAX_DRAWDOWN
        )
        
        # 7. Check risk limits
        if risk_manager.check_limits(target_position):
            # 8. Execute trade
            order = execution_engine.create_order(
                target=target_position,
                current=portfolio.positions,
                style=get_execution_style(regime)
            )
            await execution_engine.submit(order)
        
        # 9. Log everything for learning
        await monitoring.log_decision(
            features=features,
            signals=alpha_signals,
            position=target_position,
            regime=regime
        )
        
        await asyncio.sleep(config.LOOP_INTERVAL_MS / 1000)
```

### 6.2 Volatility-Targeted Position Sizer

```python
class VolatilityTargetedSizer:
    """
    Position sizing using volatility targeting.
    
    The core insight: if volatility doubles, halve the position.
    This maintains constant risk exposure.
    """
    
    def __init__(
        self,
        target_vol: float = 0.15,          # 15% annualized
        lookback_days: int = 20,
        max_leverage: float = 2.0,
        min_position: float = 0.01,
        vol_floor: float = 0.05,           # Minimum vol assumption
        vol_ceiling: float = 1.0,          # Maximum vol assumption
    ):
        self.target_vol = target_vol
        self.lookback_days = lookback_days
        self.max_leverage = max_leverage
        self.min_position = min_position
        self.vol_floor = vol_floor
        self.vol_ceiling = vol_ceiling
    
    def calculate_realized_vol(
        self, 
        returns: np.ndarray,
        annualize: bool = True
    ) -> float:
        """
        Calculate realized volatility from return series.
        
        Uses exponentially weighted moving average for
        more responsive vol estimation.
        """
        # EWMA volatility (decay factor ~0.94 for daily)
        decay = 0.94
        weights = np.array([decay ** i for i in range(len(returns))])
        weights = weights[::-1] / weights.sum()
        
        variance = np.sum(weights * (returns ** 2))
        vol = np.sqrt(variance)
        
        if annualize:
            vol *= np.sqrt(252)  # Annualize
        
        # Apply floor and ceiling
        vol = np.clip(vol, self.vol_floor, self.vol_ceiling)
        
        return vol
    
    def size_position(
        self,
        signal_strength: float,      # -1 to +1
        asset_vol: float,            # Annualized volatility
        nav: float,                  # Net Asset Value
        risk_budget_pct: float = 1.0 # Fraction of NAV to risk
    ) -> PositionSize:
        """
        Calculate position size using volatility targeting.
        
        Formula:
            position_pct = (target_vol / asset_vol) * signal_strength * risk_budget
        
        Returns both dollar amount and number of units.
        """
        # Clamp volatility to reasonable bounds
        asset_vol = np.clip(asset_vol, self.vol_floor, self.vol_ceiling)
        
        # Calculate base position (volatility-targeted)
        vol_scalar = self.target_vol / asset_vol
        
        # Apply signal strength (-1 to +1)
        raw_position_pct = vol_scalar * signal_strength * risk_budget_pct
        
        # Apply leverage constraint
        position_pct = np.clip(
            raw_position_pct,
            -self.max_leverage,
            self.max_leverage
        )
        
        # Apply minimum position threshold
        if abs(position_pct) < self.min_position:
            position_pct = 0.0
        
        # Calculate dollar amount
        position_dollars = position_pct * nav
        
        return PositionSize(
            percent_of_nav=position_pct,
            dollar_amount=position_dollars,
            vol_scalar=vol_scalar,
            raw_signal=signal_strength,
            capped=abs(raw_position_pct) != abs(position_pct)
        )
    
    def adjust_for_correlation(
        self,
        positions: Dict[str, PositionSize],
        correlation_matrix: np.ndarray,
        max_portfolio_vol: float = 0.20
    ) -> Dict[str, PositionSize]:
        """
        Scale down positions if portfolio volatility exceeds target.
        
        Portfolio vol = sqrt(w' * Σ * w)
        where Σ is the covariance matrix.
        """
        weights = np.array([p.percent_of_nav for p in positions.values()])
        vols = np.array([p.vol_scalar for p in positions.values()])
        
        # Construct covariance matrix
        vol_diag = np.diag(vols * self.target_vol)
        cov_matrix = vol_diag @ correlation_matrix @ vol_diag
        
        # Calculate portfolio volatility
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        
        # Scale if exceeds max
        if portfolio_vol > max_portfolio_vol:
            scale_factor = max_portfolio_vol / portfolio_vol
            for name, pos in positions.items():
                pos.percent_of_nav *= scale_factor
                pos.dollar_amount *= scale_factor
        
        return positions
```

### 6.3 Alpha Model Implementation

```python
class MomentumAlphaModel:
    """
    Volatility-adjusted momentum alpha model.
    
    Captures trending price movements while normalizing
    for volatility regime.
    """
    
    def __init__(
        self,
        lookbacks: List[int] = [5, 10, 20, 60],
        decay_lambda: float = 0.1,
        adx_threshold: float = 25.0,
        max_signal: float = 3.0
    ):
        self.lookbacks = lookbacks
        self.decay_lambda = decay_lambda
        self.adx_threshold = adx_threshold
        self.max_signal = max_signal
    
    def calculate_vam(
        self,
        returns: np.ndarray,
        lookback: int
    ) -> float:
        """
        Volatility-Adjusted Momentum.
        
        VAM = Σ(w_i * r_i) / σ
        where w_i are exponentially decaying weights.
        """
        if len(returns) < lookback:
            return 0.0
        
        recent_returns = returns[-lookback:]
        
        # Exponential decay weights
        weights = np.exp(-self.decay_lambda * np.arange(lookback))
        weights = weights[::-1]  # Most recent has highest weight
        weights /= weights.sum()
        
        # Weighted return
        weighted_return = np.sum(weights * recent_returns)
        
        # Volatility normalization
        vol = np.std(recent_returns)
        if vol < 1e-8:
            return 0.0
        
        return weighted_return / vol
    
    def calculate_adx(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> float:
        """
        Average Directional Index - trend strength indicator.
        """
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        
        plus_dm = np.where(
            (high[1:] - high[:-1]) > (low[:-1] - low[1:]),
            np.maximum(high[1:] - high[:-1], 0),
            0
        )
        
        minus_dm = np.where(
            (low[:-1] - low[1:]) > (high[1:] - high[:-1]),
            np.maximum(low[:-1] - low[1:], 0),
            0
        )
        
        # Smoothed averages (Wilder's smoothing)
        atr = self._wilder_smooth(tr, period)
        plus_di = 100 * self._wilder_smooth(plus_dm, period) / atr
        minus_di = 100 * self._wilder_smooth(minus_dm, period) / atr
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
        adx = self._wilder_smooth(dx, period)
        
        return adx[-1] if len(adx) > 0 else 0.0
    
    def _wilder_smooth(self, data: np.ndarray, period: int) -> np.ndarray:
        """Wilder's exponential smoothing."""
        result = np.zeros_like(data)
        result[period-1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            result[i] = (result[i-1] * (period - 1) + data[i]) / period
        
        return result[period-1:]
    
    def generate_signal(
        self,
        ohlcv: pd.DataFrame
    ) -> AlphaSignal:
        """
        Generate momentum alpha signal.
        
        Returns signal in [-max_signal, +max_signal] range.
        """
        returns = np.log(ohlcv['close'] / ohlcv['close'].shift(1)).dropna().values
        
        # Calculate VAM for each lookback
        vam_signals = []
        for lb in self.lookbacks:
            vam = self.calculate_vam(returns, lb)
            vam_signals.append(vam)
        
        # Equal-weighted average
        combined_vam = np.mean(vam_signals)
        
        # Apply ADX filter
        adx = self.calculate_adx(
            ohlcv['high'].values,
            ohlcv['low'].values,
            ohlcv['close'].values
        )
        
        if adx < self.adx_threshold:
            # Not trending enough - no signal
            return AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter='ADX_FILTER',
                components={'vam': combined_vam, 'adx': adx}
            )
        
        # Clip to max signal
        signal_value = np.clip(combined_vam, -self.max_signal, self.max_signal)
        
        # Normalize to [-1, +1] for position sizer
        normalized_signal = signal_value / self.max_signal
        
        # Confidence based on ADX strength
        confidence = min((adx - self.adx_threshold) / 25.0, 1.0)
        
        return AlphaSignal(
            value=normalized_signal,
            confidence=confidence,
            regime_filter='TRENDING',
            components={
                'vam': combined_vam,
                'adx': adx,
                'vam_by_lookback': dict(zip(self.lookbacks, vam_signals))
            }
        )


class MeanReversionAlphaModel:
    """
    Mean-reversion alpha model.
    
    Exploits temporary price dislocations from statistical
    equilibrium, with regime filtering.
    """
    
    def __init__(
        self,
        lookback: int = 20,
        entry_threshold: float = 2.0,  # Z-score threshold
        hurst_threshold: float = 0.5,
        max_signal: float = 2.5
    ):
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.hurst_threshold = hurst_threshold
        self.max_signal = max_signal
    
    def calculate_zscore(
        self,
        prices: np.ndarray
    ) -> float:
        """
        Calculate z-score of current price vs rolling mean.
        """
        if len(prices) < self.lookback:
            return 0.0
        
        recent = prices[-self.lookback:]
        current = prices[-1]
        
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std < 1e-8:
            return 0.0
        
        return (current - mean) / std
    
    def calculate_hurst(
        self,
        prices: np.ndarray,
        max_lag: int = 100
    ) -> float:
        """
        Estimate Hurst exponent via R/S analysis.
        
        H < 0.5: Mean-reverting
        H = 0.5: Random walk
        H > 0.5: Trending
        """
        if len(prices) < max_lag:
            return 0.5  # Default to random walk
        
        lags = range(2, min(max_lag, len(prices) // 2))
        rs_values = []
        
        for lag in lags:
            # Divide into subseries
            n_subseries = len(prices) // lag
            rs_list = []
            
            for i in range(n_subseries):
                subseries = prices[i*lag:(i+1)*lag]
                if len(subseries) < 2:
                    continue
                
                mean = np.mean(subseries)
                deviations = subseries - mean
                cumulative = np.cumsum(deviations)
                
                r = np.max(cumulative) - np.min(cumulative)
                s = np.std(subseries, ddof=1)
                
                if s > 1e-8:
                    rs_list.append(r / s)
            
            if rs_list:
                rs_values.append((lag, np.mean(rs_list)))
        
        if len(rs_values) < 2:
            return 0.5
        
        # Linear regression in log-log space
        log_lags = np.log([x[0] for x in rs_values])
        log_rs = np.log([x[1] for x in rs_values])
        
        slope, _ = np.polyfit(log_lags, log_rs, 1)
        
        return slope
    
    def generate_signal(
        self,
        ohlcv: pd.DataFrame
    ) -> AlphaSignal:
        """
        Generate mean-reversion signal.
        
        Negative z-score → long signal (price below mean)
        Positive z-score → short signal (price above mean)
        """
        prices = ohlcv['close'].values
        
        # Calculate Hurst exponent
        hurst = self.calculate_hurst(prices)
        
        if hurst >= self.hurst_threshold:
            # Market is trending, not mean-reverting
            return AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter='HURST_FILTER',
                components={'hurst': hurst, 'zscore': 0.0}
            )
        
        # Calculate z-score
        zscore = self.calculate_zscore(prices)
        
        # Only trade if z-score exceeds threshold
        if abs(zscore) < self.entry_threshold:
            return AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter='THRESHOLD_FILTER',
                components={'hurst': hurst, 'zscore': zscore}
            )
        
        # Mean-reversion: negative z-score → positive signal (buy)
        signal_value = -np.clip(zscore, -self.max_signal, self.max_signal)
        normalized_signal = signal_value / self.max_signal
        
        # Confidence based on how mean-reverting the series is
        confidence = (self.hurst_threshold - hurst) / self.hurst_threshold
        confidence = max(0.0, min(1.0, confidence))
        
        return AlphaSignal(
            value=normalized_signal,
            confidence=confidence,
            regime_filter='MEAN_REVERTING',
            components={
                'hurst': hurst,
                'zscore': zscore,
                'entry_threshold': self.entry_threshold
            }
        )
```

### 6.4 Risk Management Layer

```python
class RiskManager:
    """
    Central risk management with multiple safety layers.
    """
    
    def __init__(
        self,
        max_daily_loss_pct: float = 0.02,      # 2% daily loss limit
        max_drawdown_pct: float = 0.10,        # 10% max drawdown
        max_position_pct: float = 0.20,        # 20% max single position
        max_sector_exposure: float = 0.40,     # 40% max sector exposure
        max_correlation_exposure: float = 0.60 # 60% max correlated exposure
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_position_pct = max_position_pct
        self.max_sector_exposure = max_sector_exposure
        self.max_correlation_exposure = max_correlation_exposure
        
        self.daily_pnl = 0.0
        self.peak_nav = 0.0
        self.current_nav = 0.0
        self.kill_switch_active = False
    
    def update_nav(self, nav: float):
        """Update NAV and track drawdown."""
        self.current_nav = nav
        self.peak_nav = max(self.peak_nav, nav)
    
    def update_pnl(self, pnl: float):
        """Update daily P&L."""
        self.daily_pnl += pnl
    
    def reset_daily_metrics(self):
        """Called at start of each trading day."""
        self.daily_pnl = 0.0
    
    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak."""
        if self.peak_nav == 0:
            return 0.0
        return (self.peak_nav - self.current_nav) / self.peak_nav
    
    @property
    def daily_loss_pct(self) -> float:
        """Current daily loss percentage."""
        if self.current_nav == 0:
            return 0.0
        return -self.daily_pnl / self.current_nav if self.daily_pnl < 0 else 0.0
    
    def check_limits(self, proposed_position: PositionSize) -> RiskCheckResult:
        """
        Check all risk limits before allowing a trade.
        
        Returns RiskCheckResult with approval status and reasons.
        """
        violations = []
        
        # 1. Kill switch check
        if self.kill_switch_active:
            return RiskCheckResult(
                approved=False,
                violations=['KILL_SWITCH_ACTIVE'],
                adjusted_position=None
            )
        
        # 2. Daily loss limit
        if self.daily_loss_pct >= self.max_daily_loss_pct:
            violations.append(f'DAILY_LOSS_LIMIT: {self.daily_loss_pct:.2%}')
            self._activate_kill_switch('Daily loss limit breached')
        
        # 3. Drawdown limit
        if self.current_drawdown >= self.max_drawdown_pct:
            violations.append(f'MAX_DRAWDOWN: {self.current_drawdown:.2%}')
        
        # 4. Single position size limit
        if abs(proposed_position.percent_of_nav) > self.max_position_pct:
            violations.append(
                f'POSITION_SIZE: {proposed_position.percent_of_nav:.2%} > '
                f'{self.max_position_pct:.2%}'
            )
        
        if violations:
            return RiskCheckResult(
                approved=False,
                violations=violations,
                adjusted_position=None
            )
        
        return RiskCheckResult(
            approved=True,
            violations=[],
            adjusted_position=proposed_position
        )
    
    def scale_for_risk(
        self,
        position: PositionSize,
        current_risk_utilization: float
    ) -> PositionSize:
        """
        Scale position based on current risk utilization.
        
        As we approach limits, gradually reduce position sizes.
        """
        # Calculate headroom
        dd_headroom = (self.max_drawdown_pct - self.current_drawdown) / self.max_drawdown_pct
        daily_headroom = (self.max_daily_loss_pct - self.daily_loss_pct) / self.max_daily_loss_pct
        
        # Minimum headroom determines scale
        scale_factor = max(0.0, min(dd_headroom, daily_headroom))
        
        # Apply non-linear scaling (more aggressive reduction near limits)
        scale_factor = scale_factor ** 0.5
        
        return PositionSize(
            percent_of_nav=position.percent_of_nav * scale_factor,
            dollar_amount=position.dollar_amount * scale_factor,
            vol_scalar=position.vol_scalar,
            raw_signal=position.raw_signal,
            capped=True
        )
    
    def _activate_kill_switch(self, reason: str):
        """Activate emergency kill switch."""
        self.kill_switch_active = True
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        # In production: send alerts, close all positions, etc.
```

### 6.5 Regime Detection

```python
class RegimeDetector:
    """
    Detects market regime for strategy selection.
    
    Regimes:
    - TRENDING_UP / TRENDING_DOWN
    - MEAN_REVERTING
    - HIGH_VOLATILITY
    - LOW_VOLATILITY
    - CRISIS
    """
    
    def __init__(
        self,
        vol_lookback: int = 20,
        trend_lookback: int = 50,
        vol_percentile_low: float = 25,
        vol_percentile_high: float = 75,
        adx_threshold: float = 25,
        hurst_threshold: float = 0.5
    ):
        self.vol_lookback = vol_lookback
        self.trend_lookback = trend_lookback
        self.vol_percentile_low = vol_percentile_low
        self.vol_percentile_high = vol_percentile_high
        self.adx_threshold = adx_threshold
        self.hurst_threshold = hurst_threshold
        
        self.vol_history = []
    
    def classify(self, features: Dict[str, float]) -> MarketRegime:
        """
        Classify current market regime.
        """
        vol = features.get('realized_vol', 0.15)
        adx = features.get('adx', 0)
        hurst = features.get('hurst', 0.5)
        trend_direction = features.get('trend_direction', 0)
        
        # Update volatility history
        self.vol_history.append(vol)
        if len(self.vol_history) > 252:  # Keep 1 year
            self.vol_history = self.vol_history[-252:]
        
        # Calculate volatility percentile
        vol_percentile = self._calculate_percentile(vol, self.vol_history)
        
        # Crisis detection (extreme volatility + negative returns)
        if vol_percentile > 95 and trend_direction < -0.5:
            return MarketRegime.CRISIS
        
        # Volatility regime
        if vol_percentile < self.vol_percentile_low:
            vol_regime = 'LOW'
        elif vol_percentile > self.vol_percentile_high:
            vol_regime = 'HIGH'
        else:
            vol_regime = 'NORMAL'
        
        # Trend vs mean-reversion
        if adx > self.adx_threshold and hurst > self.hurst_threshold:
            if trend_direction > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN
        elif hurst < self.hurst_threshold:
            return MarketRegime.MEAN_REVERTING
        
        # Default to volatility regime
        if vol_regime == 'HIGH':
            return MarketRegime.HIGH_VOLATILITY
        elif vol_regime == 'LOW':
            return MarketRegime.LOW_VOLATILITY
        
        return MarketRegime.NORMAL
    
    def _calculate_percentile(self, value: float, history: List[float]) -> float:
        """Calculate percentile of value in historical distribution."""
        if not history:
            return 50.0
        return 100 * sum(1 for x in history if x <= value) / len(history)
    
    def get_strategy_weights(self, regime: MarketRegime) -> Dict[str, float]:
        """
        Get strategy weights based on current regime.
        
        Returns weights for [momentum, mean_reversion, volatility_breakout].
        """
        weights = {
            MarketRegime.TRENDING_UP: {'momentum': 0.7, 'mean_reversion': 0.1, 'vol_breakout': 0.2},
            MarketRegime.TRENDING_DOWN: {'momentum': 0.7, 'mean_reversion': 0.1, 'vol_breakout': 0.2},
            MarketRegime.MEAN_REVERTING: {'momentum': 0.1, 'mean_reversion': 0.7, 'vol_breakout': 0.2},
            MarketRegime.HIGH_VOLATILITY: {'momentum': 0.3, 'mean_reversion': 0.2, 'vol_breakout': 0.5},
            MarketRegime.LOW_VOLATILITY: {'momentum': 0.4, 'mean_reversion': 0.5, 'vol_breakout': 0.1},
            MarketRegime.CRISIS: {'momentum': 0.0, 'mean_reversion': 0.0, 'vol_breakout': 0.0},  # Cash
            MarketRegime.NORMAL: {'momentum': 0.4, 'mean_reversion': 0.4, 'vol_breakout': 0.2},
        }
        return weights.get(regime, weights[MarketRegime.NORMAL])
```

---

## 7. Continuous Learning Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONTINUOUS LEARNING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │  LIVE TRADING   │──────────────┐                                         │
│  │                 │              │                                         │
│  │ • Execute trades│              ▼                                         │
│  │ • Log decisions │    ┌─────────────────────┐                             │
│  │ • Track fills   │    │   DECISION LOG DB   │                             │
│  └─────────────────┘    │                     │                             │
│           │             │ • Features snapshot │                             │
│           │             │ • Model predictions │                             │
│           │             │ • Actual outcomes   │                             │
│           │             │ • Execution quality │                             │
│           │             └──────────┬──────────┘                             │
│           │                        │                                        │
│           ▼                        ▼                                        │
│  ┌─────────────────┐    ┌─────────────────────┐                             │
│  │  REAL-TIME      │    │  NIGHTLY BATCH      │                             │
│  │  MONITORING     │    │  EVALUATION         │                             │
│  │                 │    │                     │                             │
│  │ • PnL tracking  │    │ • Walk-forward test │                             │
│  │ • Drift detect  │    │ • Model comparison  │                             │
│  │ • Regime alerts │    │ • Feature importance│                             │
│  └────────┬────────┘    └──────────┬──────────┘                             │
│           │                        │                                        │
│           ▼                        ▼                                        │
│  ┌─────────────────────────────────────────────┐                            │
│  │           MODEL SELECTION BANDIT            │                            │
│  │                                             │                            │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │                            │
│  │  │Model A  │ │Model B  │ │Model C  │       │                            │
│  │  │Sharpe:  │ │Sharpe:  │ │Sharpe:  │       │                            │
│  │  │ 1.8     │ │ 2.1     │ │ 1.5     │       │                            │
│  │  │Weight:  │ │Weight:  │ │Weight:  │       │                            │
│  │  │ 25%     │ │ 50%     │ │ 25%     │       │                            │
│  │  └─────────┘ └─────────┘ └─────────┘       │                            │
│  │                                             │                            │
│  │  Thompson Sampling / UCB for capital alloc  │                            │
│  └─────────────────────────────────────────────┘                            │
│                        │                                                    │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────┐                            │
│  │         MODEL PROMOTION / DEMOTION          │                            │
│  │                                             │                            │
│  │  PROMOTE if:                                │                            │
│  │  • OOS Sharpe > threshold (e.g., 1.5)      │                            │
│  │  • No drift detected                        │                            │
│  │  • Stable across regimes                    │                            │
│  │                                             │                            │
│  │  DEMOTE if:                                 │                            │
│  │  • Rolling Sharpe < 0.5 over 20 trades     │                            │
│  │  • Feature drift detected                   │                            │
│  │  • Systematic underperformance              │                            │
│  └─────────────────────────────────────────────┘                            │
│                        │                                                    │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────┐                            │
│  │           RETRAINING PIPELINE               │                            │
│  │                                             │                            │
│  │  Weekly retraining on rolling window:       │                            │
│  │  • Last 6 months of data                    │                            │
│  │  • Purged cross-validation                  │                            │
│  │  • Walk-forward validation                  │                            │
│  │                                             │                            │
│  │  Candidate models deployed to:              │                            │
│  │  • Shadow trading (paper trades)            │                            │
│  │  • A/B test with small capital              │                            │
│  └─────────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Deployment Architecture

```yaml
# docker-compose.trading.yml
version: '3.8'

services:
  # Message Queue
  kafka:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    volumes:
      - kafka-data:/var/lib/kafka/data
  
  # Hot Storage
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
  
  # Time-Series Database
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - timescale-data:/var/lib/postgresql/data
  
  # Feature Engine
  feature-engine:
    build: ./backend/trading/features
    depends_on:
      - kafka
      - redis
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      REDIS_URL: redis://redis:6379
  
  # Alpha Models
  alpha-service:
    build: ./backend/trading/alpha_models
    depends_on:
      - feature-engine
      - redis
    deploy:
      replicas: 2
  
  # Risk Manager
  risk-service:
    build: ./backend/trading/risk
    depends_on:
      - alpha-service
    environment:
      MAX_DAILY_LOSS: 0.02
      MAX_DRAWDOWN: 0.10
  
  # Execution Engine
  execution-engine:
    build: ./backend/trading/execution
    depends_on:
      - risk-service
    environment:
      EXCHANGE_API_KEY: ${EXCHANGE_API_KEY}
      EXCHANGE_SECRET: ${EXCHANGE_SECRET}
  
  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    depends_on:
      - prometheus
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/dashboards:/var/lib/grafana/dashboards

volumes:
  kafka-data:
  redis-data:
  timescale-data:
```

---

## 9. Key Implementation Principles

### 9.1 No Look-Ahead Bias
- All features computed with point-in-time data only
- Strict timestamp ordering in backtests
- Purged cross-validation for overlapping labels

### 9.2 Transaction Cost Awareness
- Include realistic bid-ask spreads
- Model market impact (linear/square-root)
- Account for fees, funding rates, borrow costs

### 9.3 Regime Awareness
- Separate models for different market conditions
- Dynamic strategy allocation based on regime
- Automatic deactivation in crisis regimes

### 9.4 Defense in Depth
- Multiple layers of risk checks
- Hard limits enforced outside ML models
- Human-in-the-loop for parameter changes

### 9.5 Continuous Monitoring
- Real-time drift detection
- Model performance degradation alerts
- Automatic model demotion when underperforming

---

## 10. Summary

This architecture provides:

1. **Modularity**: Each component (data, features, alpha, risk, execution) is independent and testable
2. **Scalability**: Kafka-based event streaming allows horizontal scaling
3. **Robustness**: Multiple layers of risk management prevent catastrophic losses
4. **Adaptability**: Regime detection and online learning adapt to changing markets
5. **Auditability**: Every decision is logged with full feature context

The "living lab" design ensures the system continuously learns and improves while maintaining strict risk controls.
