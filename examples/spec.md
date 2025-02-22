# Git Metrics Tracker - Project Specification

To assist in determining the impact of introducing various AI coding assistants, this project will collect metrics that can be used to analyze the impact of these tools on a project. Additionally, it will attempt to determine if there are significant changes in metrics compared to the historical baseline.

## General Requirements:
- Collect and store Git activity metrics in **sprint periods** (number of days in period and day of week of start of period are configurable).
- Metrics should include:
  - **Lines of Code (LOC) added**
  - **LOC deleted**
  - **Number of commits**
  - **Number of pull requests (PRs)**
  - **Average PR review time**
  - **Per-committer breakdown of these metrics**
- Support multiple repositories from different Git platforms, as configured in a **YAML file**.
- **Cache** data locally to avoid re-fetching history from the beginning.
- **Generate an Excel report** with:
  - A **summary sheet** aggregating metrics across all repositories.
  - **Per-repo sheets**, structured in **two-week intervals** with collected stats.
  - Headers rotated **90 degrees** for better readability and **columns set to minimal width**.
- **Compute descriptive statistics** for each repo and **highlight significant deviations**.

## Technical Specifications:

### 1. Data Collection
- Use Git CLI or APIs to extract data.
- Authenticate with different Git providers using credentials from a **YAML configuration file**.
- Compute **LOC changes** using:
  ```bash
  git log --numstat
  ```
- Extract **PR review times** via Git provider APIs.
- Cache fetched data to avoid redundant API calls.

### 2. Configuration
- `config.yaml` should contain:
  - Authentication credentials (token or username/password) for each Git provider.
  - A list of repositories to track, mapped to their respective provider.
  - The **output filename** for the generated report.
  - The **directory** to store cached data.
  - The **day of week in previous week** used to indicate collection period start.
  - The **number of days** in a collection period.
  - The **number of standard deviations** from the mean to highlight significant deviations.

### 3. Data Storage & Processing
- Store fetched data locally in a structured format (**SQLite or JSON**).
- Efficient querying for historical data.

### 4. Statistical Analysis & Deviation Highlighting
- Compute **descriptive statistics** (mean, median, standard deviation) for each metric in repositories with sufficient activity.
- Identify **significant deviations** in any period where values differ from the norm by more than a set threshold (e.g., **two standard deviations**).
- **Highlight** these deviations in the Excel report.

### 5. Excel Report Generation
- Use **`pandas`** and **`openpyxl`** to create an Excel report.
- Include a **summary sheet** aggregating metrics across all repositories.
- Each repository should have its own sheet, formatted as follows:
  ```
  | Period Start | Period End | LOC Added | LOC Deleted | Commits | PRs | Avg PR Review Time | [Committer1 LOC Added] | [Committer1 LOC Deleted] | ...
  ```
- **Headers rotated 90 degrees** for better readability.
- **Highlight significant deviations** from norms in red.
- **Minimum column width** set automatically based on the longest data width in any given column.

---

## Code Quality & Testing

### 6. Testing Framework
- Use **`pytest`** for unit tests.
- Ensure **80%+ test coverage**.

### 7. Pre-commit Hooks
- Use **`pre-commit`** to enforce code quality checks.
- Set up hooks to run:
  - **`black`** (auto-formatting)
  - **`flake8`** (linting)
  - **`mypy`** (type checking)
  - **`isort`** (import sorting)

- Example `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/psf/black
      rev: 23.1.0
      hooks:
        - id: black
    - repo: https://github.com/PyCQA/flake8
      rev: 6.0.0
      hooks:
        - id: flake8
    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.2.0
      hooks:
        - id: mypy
    - repo: https://github.com/PyCQA/isort
      rev: 5.12.0
      hooks:
        - id: isort
  ```

### 8. Performance Considerations
- Implement **caching** to avoid redundant API calls.
- Process repositories **in parallel** where possible.

### 9. Installation & Usage
- Provide a CLI tool to run the report generation.
- A script to run the analysis and generate the report should be included in the package installation (e.g. entrypoint in setup.py, etc.)
- Include a **`README.md`** with setup instructions.

### 10. Packaging
- Must use **uv** for managing the packaging, virtual env, etc.
- The package name should be **`ai_coding_metrics`**.

### 11. Licensing
- **License the project under the MIT License**.
- Include a `LICENSE` file with the following content:
  ```
  MIT License

  Copyright (c) 2025

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
  ```

This ensures **high code quality, test coverage, statistical analysis, and efficient data handling**.

