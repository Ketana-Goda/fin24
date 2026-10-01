\# PLUTO24: Recurring Expense \& Subscription Intelligence (FIN-24)



Upload historical transactions. The system finds recurring commitments, forecasts

upcoming payments, flags possible duplicates and price increases, tracks renewals

by department, and answers questions from the data.



\## Features

\- \*\*Recurring detection:\*\* weekly, monthly, quarterly and yearly patterns from

&#x20; payment timing and amount consistency (Pandas, no black-box ML)

\- \*\*Subscription registry:\*\* monthly and annual cost, department, next renewal,

&#x20; days to renewal, Renew / Review / Cancel decisions (saved), estimated saving

\- \*\*Forecast:\*\* expected payments for the next 7, 30 and 90 days

\- \*\*Alerts:\*\* overlapping subscriptions, price increases, stopped payments, each

&#x20; with the underlying transactions

\- \*\*Finance Assistant:\*\* answers questions using our calculation functions, so

&#x20; numbers are never invented

\- \*\*Aczen API integration:\*\* invoice monitoring on the live Nova API data



\## Data note

The provided Aczen slice contained sales invoices (money received), not expense

records, so it holds no recurring-expense patterns. We validated detection on a

synthetic expense ledger with known ground truth (`generate\_data.py`). The app

accepts any CSV with columns: date, vendor, category, amount (optional: department).



\## Limitations

\- No usage data, so utilization is not assessed. Flags rely on payment patterns only.

\- Flags say "potential overlap, requires review". The final decision is the finance team's.



\## Run

&#x20;   pip install -r requirements.txt

&#x20;   py generate\_data.py

&#x20;   py add\_department.py

&#x20;   py -m streamlit run app.py



Put NOVA\_API\_KEY and NOVA\_BASE\_URL in a `.env` file (not committed).

