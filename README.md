# UST-Market

# UST Market — 2-Year Treasury (2018-01-08)

This project merges and sorts U.S. Treasury 2-Year event data for January 8 2018.  
It combines **Order Change (OC)**, **Trade (T)**, and **Work-Up (WU)** files into one chronologically ordered CSV using the tie-break rule **OC → WU → T**.

## How to Run
```bash
python merge.py
