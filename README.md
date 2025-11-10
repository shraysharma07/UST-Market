# UST-Market (October 28th 2025)

# UST Market — 2-Year Treasury (2018-01-08)

This project merges and sorts U.S. Treasury 2-Year event data for January 8 2018.  
It combines **Order Change (OC)**, **Trade (T)**, and **Work-Up (WU)** files into one chronologically ordered CSV using the tie-break rule **OC → WU → T**.

## How to Run
```bash
python merge.py

# Sprint 3 – Order Identification and Market Direction (November 5th 2025)

This sprint analyzes market direction using order book data from `OC_2_20180108.csv`.

### How It Works
- Reads raw order data.
- Determines **side** (`B` = buy, `A` = sell).
- Calculates:
  - **Action** = ±Quantity  
  - **PositionTaken** = Quantity × Premium (256ths)  
  - **Cumulative Position** = running total  
  - **Direction** = Up / Down / Flat (based on cumulative change)

### Example Output
| Seq | Action | Premium | PositionTaken | Cumulative | Side | Direction |
|-----|---------|----------|----------------|-------------|------|------------|
| 1 | +5 | 25552 | +127760 | +127760 | B | Up |
| 6 | -5 | 25562 | -127810 | +383150 | A | Down |

### Run
```bash
python sprint3_generate_positions.py
