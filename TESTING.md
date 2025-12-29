# Testing Guide

This project maintains a structured testing environment to ensure reliability across backend logic, AI integration, and chart calculations.

## Test Directory Structure

The `tests/` directory is organized into the following subdirectories:

- **`tests/backend/`**: Contains core unit tests for astrology logic, chart rendering, and API endpoints.
  - `test_astrology_validation.py`: Verifies input validation (dates, locations).
  - `test_north_indian_chart.py`: Tests the North Indian chart rendering logic and Chara Karaka calculations.
  - `test_varga_calculations.py`: Validates divisional chart (Varga) math.
  - `test_backend.py`: General integration tests.
  - `test_al_logic.py`: Logic checks for Arudha Lagna specific cases.

- **`tests/ai/`**: Contains tests for the AI prediction engine.
  - `test_ai.py`: Tests parsing of AI responses and logic flow.

- **`tests/tools/`**: Contains manual verification scripts causing side-effects (e.g., generating images, printing tables).
  - `verify_calculations.py`: Prints detailed planetary tables to stdout for manual checking.
  - `verify_render.py`: Generates chart images in `test_outputs/` or `generated_charts/` for visual inspection.

## How to Run Tests

### 1. Run All Automated Tests
To run all automated unit tests using `pytest` (recommended):
```bash
python3 -m pytest tests
```

### 2. Run Backend Tests Only
```bash
python3 -m pytest tests/backend
```

### 3. Run AI Tests
```bash
python3 tests/ai/test_ai.py
```

### 4. Run Verification Tools
These scripts output data or files for manual inspection.

**Verify Calculations (Prints Table):**
```bash
python3 tests/tools/verify_calculations.py
```

**Verify Rendering (Generates Images):**
```bash
python3 tests/tools/verify_render.py
```

## Adding New Tests
- **Logic Tests**: Add to `tests/backend/` prefixing the filename with `test_`.
- **AI Tests**: Add to `tests/ai/`.
- **Manual Tools**: Add to `tests/tools/`.
