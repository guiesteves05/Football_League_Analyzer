# Football Championship LP Analyzer

This project was developed, in Python, for the Analysis and Algorithms Synthesis course in January 2026. The tool acts as an analytical engine for a fictional company, SnailSoft, to evaluate team standings in a football championship. This project helped me learn the basics on Linear Programming.

## Problem Description
The goal is to calculate the absolute minimum number of additional games a specific team must win to mathematically secure the championship (assuming all other match outcomes are favorable to them). 

*   The championship consists of two symmetric rounds where all teams play each other twice (home and away).
*   Points are awarded as follows: 3 points for a win, 1 point for a draw, and 0 points for a loss.

## Implementation
The problem is modeled and solved using Linear Programming (LP). 
*   **Language**: Python.
*   **Library**: `PuLP` is used to formulate the integer linear programming model.
*   **Solver**: The script uses the Coin-or-branch-and-cut (CBC) solver configured for a single thread (`pulp.PULP_CBC_CMD(msg=0, threads=1)`).

## Setup & Execution

**1. Install dependencies:**
Requires the PuLP library and an LP solver (like GLPK or CBC).
`python3 -m pip install pulp`

**2. Run the script:**
`python3 LigaBetclic.py < input.txt`

## Input / Output Format
*   **Input**: The first line contains the number of teams (`n`) and matches played (`m`). The following `m` lines detail the matches with the home team, away team, and the result (winning team ID, or 0 for a draw).
*   **Output**: Outputs `n` lines containing the minimum wins required for each team. If a team cannot mathematically win the championship, it outputs `-1`.