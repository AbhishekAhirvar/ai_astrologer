# AI Astrologer: Advanced Engineering Architecture & Logic Guide

> **Target Audience**: C++/DSA/ML Engineers.
> **Goal**: To decompose the codebase into algorithmic components, analyze complexity, and identify optimization vectors.

This is not a "getting started" guide. This is an **system internals** manual.

---

## 1. System Architecture & Memory Model

### The Python-C++ Bridge
While this is a pure Python project, the "Heavy Lifting" is done by C.
*   **Layer 1 (Drivers)**: `swisseph` (Swiss Ephemeris). This is a C extension.
*   **Layer 2 (Controller)**: `backend/astrology.py`. Python glue code.
*   **Layer 3 (Compute)**: `backend/varga_charts.py`. Pure Python algorithmic layer.

**Performance Implication**:
*   Calls to `swisseph.*` are fast ($O(1)$) but cross the C-API boundary (GIL overhead).
*   AI interpretation is asynchronous and streamed to minimize perceived latency.

> **Architecture Quiz (Q1)**:
> In `app.py`, we store `user_requests = defaultdict(list)` as a global in-memory state.
> *   **Critique**: How does this behave in a multi-process deployment (e.g., Gunicorn with 4 workers)?
> *   **Refactor**: Design a Redis-based rate limiter to replace this $O(1)$ Python dict.

---

## 2. Core Module: `astrology.py` (The Physics Engine)

### 2.1 Coordinate Systems
The Swiss Ephemeris returns **Ecliptic Longitude** (0 to 360 degrees).
We convert this to **Zodiacal Coordinates** (Sign + Degree).

```
Sign ID = floor(Longitude / 30) % 12
Degree  = Longitude % 30
```

### 2.2 Precision Engineering
We treat planetary positions as `float`.
*   **Vulnerability**: Floating point drift.
*   **Scenario**: A planet at `29.999999` degrees.
    *   `int(29.999999) -> 29`.
    *   If we round too early: `round(29.9999, 2) -> 30.00`.
    *   `int(30.00) -> 30`. This is **invalid** (Signs are 0-29).
*   **Check Code**: `backend/varga_charts.py:56` -> `degree = min(degree, 29.9999)`.

### 2.3 Algorithmic Complexity
*   **Input Validation**: `O(1)`.
*   **Planetary Calc**: `9 * C_swe`, where `C_swe` is the constant time C-call.
*   **Compound Relationship**: Nested Loop.
    *   Top loop: 9 planets.
    *   Inner search: Linear scan over 9 planets to find `lord_sign`.
    *   Total: `O(P^2)` where `P=9`. It is trivial now, but inefficient for `N=1000` asteroids.

> **Deep Dive Questions**:
> 1.  **Bitwise Ops**: Can `NATURAL_RELATIONSHIPS` (Friend=1, Neutral=0, Enemy=-1) be encoded into a 2-bit struct to save memory?
> 2.  **Ephemeris**: `calculate_julian_day` handles Timezones. If we didn't use `pytz`, how would you calculate Julian Day from Unix Timestamp in C++?
> 3.  **Refactoring**: Rewrite `calculate_compound_relationship` to use an $O(1)$ Lookup Table (Pre-computed hashmap) instead of the dynamic search.

---

## 3. Core Module: `varga_charts.py` (The Divisional Logic)

This is the **Algorithmic Heart**.

### 3.1 The Mapping Function
A "Varga" chart maps a degree `D` in `[0, 30)` in Sign `S` to a new Sign `S'`.
General Formula for `D_N` chart:

```
DivIndex = floor((Degree * N) / 30)
S'       = (StartSignRule(S) + DivIndex) % 12
```

### 3.2 Recursive Complexity
We calculate 16+ varga charts sequentially.
*   **Current State**: Sequential execution.
*   **Pattern**: Transformations are independent.
*   **Optimization**: This is embarrassingly parallel.
*   **Vectorization**: Could we use `numpy` to broadcast the division operation across all planets simultaneously?

### 3.3 The "Chara Karaka" Sorting
In `chart_renderer.py` (moved recently), we sort planets by degree.
```python
planet_degrees.sort(key=lambda x: (-x[1], x[0]))
```
*   **Requirement**: Strict ordering.
*   **Edge Case**: Two planets at exactly `12.34` degrees.
*   **Stability**: The sort is stable in Python (Timsort).
*   **Tie-Breaker**: The `x[0]` (Name) acts as the deterministic tie-breaker.

> **Deep Dive Questions**:
> 1.  **Modular Arithmetic**: In `calculate_d9_navamsa`, look at the `movable_fixed_dual` rule. Could this `if-else` chain be replaced by a mathematical function of `sign_num % 3`?
>     *   *Hint*: `0, 3, 6, 9 % 3 = 0`. `1, 4, 7, 10 % 3 = 1`.
> 2.  **Boundary Conditions**: What happens if `divisor` is 0? The code checks `if divisor <= 0`. In C++, this would be a division by zero error (SIGFPE).
> 3.  **Jaimini System**: `calculate_arudha_lagna` has exception triggers (`if dist == 0`, `if dist == 6`). This is a state machine logic. Draw the state transition diagram for this function.

---

## 4. Core Module: `chart_renderer.py` (Graphics Engine)

### 4.1 The North Indian Diamond
This is a **Geometric Transformation** problem.
*   **Space**: Non-Euclidean topology (Astrological houses are discrete, but drawn as continuous polygons).
*   **Projection**:
    *   House 1 is the Top Diamond.
    *   House 4 is the Right (or Bottom) Triangle depending on rotation.
*   **Implementation**: Hardcoded vertices in `draw_structure()`.

### 4.2 Text Collision & Viewport
*   **Problem**: Placing "Sun 10°" and "Mer 11°" in the same house.
*   **Current Sol**: `get_positions_in_house`.
    *   It calculates offsets dynamically based on `len(planets)`.
*   **Collision Detection**: None. It just spaces them out.

> **Deep Dive Questions**:
> 1.  **Linear Algebra**: The `diamond_x` and `diamond_y` lists define a polygon. Write a C++ function `bool isInside(Point p, Polygon poly)` to verify if a planet placement falls inside the visual boundary.
> 2.  **Object Pooling**: `plt.subplots` creates heavy objects. If we generate 1000 charts/sec, memory leaks. How does `plt.close(self.fig)` relate to `delete` in C++?
> 3.  **Inheritance**: `NorthIndianChart` is a standalone class. If we wanted to add `SouthIndianChart` (Square format), should we use an abstract base class `BaseChart`? What methods would be pure virtual?

---

## 5. Security & QA poking

### 5.1 Input Fuzzing
*   **Date Injection**: What if `month` is `-1`? (Handled by `validate_input`).
*   **Overflow**: What if `year` is `99999`? `swisseph` might segfault or return garbage.

### 5.2 Thread Safety
*   The `swisseph` library is **stateful** (`swe.set_sid_mode`).
*   **Race Condition**:
    *   Thread A calls `set_sid_mode(LAHIRI)`.
    *   Thread B calls `set_sid_mode(TROPICAL)`.
    *   Thread A calculates position -> **WRONG DATA**.
*   **Fix**: Use a threading lock (`threading.Lock`) around the generic `swisseph` calls, or use context managers.

---

## 6. Advanced Coding Challenges (Homework)

### Challenge 1: The Fast-Path Varga Calculator
Rewrite `calculate_all_vargas` to use a single loop pass.
Instead of calling `calculate_varga` specific functions, use a `RuleArray` config:
```cpp
struct VargaRule { int divisor; int start_offset; };
```
Implement a generic engine that takes this struct and computes any D-Chart without specialized functions.

### Challenge 2: Thread-Safe Ephemeris
Wrap the `swisseph` calls in a Class that implements the **Singleton Pattern** with a **Mutex**.
Prove that 10 concurrent requests do not corrupt the Ayanamsa setting.

### Challenge 3: Fractal Charting
The D-charts (D9, D10) are charts themselves.
Modify `NorthIndianChart` to support **Recursion**:
*   Draw the D1 chart.
*   Inside House 1 of D1, draw a tiny D9 charts.
*   (This requires mastering the coordinate systems `ax.inset_axes`).
