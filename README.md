# Bank Resilience Dashboard

A Streamlit dashboard analyzing the 2025 Federal Reserve DFAST Stress-Test results to assess bank resilience and provide actionable insights for corporate treasurers and financial decision-makers.

## Problem: "The Corporate Treasurer's Dilemma"

Imagine you are the Treasurer of a mid-sized tech company (like Roku or Etsy) sitting on $500 million in payroll cash. After the collapse of Silicon Valley Bank (SVB), you can no longer blindly trust that "a bank is a bank." You have a fiduciary duty to ensure that your company's money doesn't vanish overnight.

**The Fear:** If the economy crashes (Severely Adverse Scenario), will the bank blocking your payroll accounts be seized by regulators?

**The Gap:** Credit ratings (like "AA-") are slow to react. Stock price is too volatile. You need a structural view of safety.

**How The "Resilience" Analysis Solves It:** The analysis provides a "Survival Scorecard."

- **Quantifiable Safety:** Instead of guessing, you can say: "Bank A burns 40% of its equity in a crash, leaving it with only 1% wiggle room. Bank B only burns 10% and stays fully capitalized."

- **Counterparty Risk Limit:** You can use your "Stress Delta" to set limits. "We will only deposit funds in banks that maintain a >2% buffer after a theoretical crash."

- **The "Flight to Quality" Map:** The scatter plot literally maps where you should move your money. You move funds from the bottom-right (High Risk) to the top-left (Fortress).

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch the Streamlit app:
   ```bash
   streamlit run app.py
   ```

3. Open your browser and navigate to the local URL displayed in the terminal (typically `http://localhost:8501`).
