import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ACZEN_API_KEY")
BASE_URL = os.getenv("ACZEN_BASE_URL")


def load_invoices():
    url = BASE_URL + "/invoices?limit=300"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    return pd.DataFrame(data["data"])


def ask_question(question, df):

    question = question.lower().strip()

    # 1. Overdue invoices
    if "overdue" in question:
        overdue = df[df["status"] == "overdue"]

        count = len(overdue)
        amount = overdue["balance_due"].sum()

        return (
            f"There are {count} overdue invoices "
            f"with a total outstanding amount of ₹{amount:,.2f}."
        )

    # 2. Pending invoices
    elif "pending" in question:
        pending = df[df["status"] == "pending"]

        count = len(pending)
        amount = pending["balance_due"].sum()

        return (
            f"There are {count} pending invoices "
            f"with a total outstanding amount of ₹{amount:,.2f}."
        )

    # 3. Paid invoices
    elif "paid invoices" in question:
        paid = df[df["status"] == "paid"]

        count = len(paid)
        amount = paid["paid_amount"].sum()

        return (
            f"There are {count} paid invoices "
            f"with a total paid amount of ₹{amount:,.2f}."
        )

    # 4. Highest outstanding client
    elif (
        "highest outstanding" in question
        or "owes the most" in question
        or "most outstanding" in question
        or "largest outstanding" in question
    ):
        client_data = (
            df.groupby("client_name")["balance_due"]
            .sum()
            .sort_values(ascending=False)
        )

        client = client_data.index[0]
        amount = client_data.iloc[0]

        return (
            f"{client} has the highest outstanding amount "
            f"of ₹{amount:,.2f}."
        )

    # 5. Total invoice amount
    elif (
        "total invoice" in question
        or "total invoiced" in question
        or "total invoice amount" in question
    ):
        total = df["total_amount"].sum()

        return f"The total invoice amount is ₹{total:,.2f}."

    # 6. Total paid amount
    elif (
        "total paid" in question
        or "amount paid" in question
        or "how much paid" in question
    ):
        total = df["paid_amount"].sum()

        return f"The total paid amount is ₹{total:,.2f}."

    # 7. Total outstanding amount
    elif (
        "total outstanding" in question
        or "outstanding amount" in question
        or "how much is outstanding" in question
        or "money outstanding" in question
    ):
        total = df["balance_due"].sum()

        return f"The total outstanding amount is ₹{total:,.2f}."

    # 8. Number of invoices
    elif (
        "how many invoices" in question
        or "number of invoices" in question
        or "invoice count" in question
    ):
        count = len(df)

        return f"There are {count} invoices in the dataset."

    # 9. Total number of clients
    elif (
        "how many clients" in question
        or "number of clients" in question
        or "client count" in question
    ):
        count = df["client_name"].nunique()

        return f"There are {count} unique clients in the dataset."

    # 10. Client-specific information
    elif any(
        word in question
        for word in [
            "client",
            "invoices from",
            "invoice from",
            "about"
        ]
    ):

        for client_name in df["client_name"].dropna().unique():

            if client_name.lower() in question:

                client_data = df[
                    df["client_name"].str.lower() == client_name.lower()
                ]

                total = client_data["total_amount"].sum()
                paid = client_data["paid_amount"].sum()
                outstanding = client_data["balance_due"].sum()

                return (
                    f"{client_name} has {len(client_data)} invoices. "
                    f"Total invoice amount is ₹{total:,.2f}. "
                    f"Paid amount is ₹{paid:,.2f}. "
                    f"Outstanding amount is ₹{outstanding:,.2f}."
                )

        return "I couldn't find that client in the invoice data."

    # 11. Invoice-specific information
    elif "inv-" in question:

        for invoice_number in df["invoice_number"].dropna():

            if invoice_number.lower() in question:

                invoice = df[
                    df["invoice_number"].str.lower()
                    == invoice_number.lower()
                ].iloc[0]

                return (
                    f"Invoice {invoice['invoice_number']} "
                    f"belongs to {invoice['client_name']}. "
                    f"Total amount: ₹{invoice['total_amount']:,.2f}. "
                    f"Paid amount: ₹{invoice['paid_amount']:,.2f}. "
                    f"Outstanding: ₹{invoice['balance_due']:,.2f}. "
                    f"Status: {invoice['status']}. "
                    f"Invoice date: {invoice['invoice_date']}. "
                    f"Due date: {invoice['due_date']}."
                )

        return "I couldn't find that invoice in the data."

    # 12. Show all overdue invoice details
    elif (
        "show overdue" in question
        or "list overdue" in question
        or "overdue invoices details" in question
    ):

        overdue = df[df["status"] == "overdue"]

        if len(overdue) == 0:
            return "There are no overdue invoices."

        result = "Overdue invoices:\n\n"

        for _, row in overdue.head(10).iterrows():

            result += (
                f"{row['invoice_number']} - "
                f"{row['client_name']} - "
                f"₹{row['balance_due']:,.2f}\n"
            )

        return result

    # 13. Show pending invoice details
    elif (
        "show pending" in question
        or "list pending" in question
        or "pending invoices details" in question
    ):

        pending = df[df["status"] == "pending"]

        if len(pending) == 0:
            return "There are no pending invoices."

        result = "Pending invoices:\n\n"

        for _, row in pending.head(10).iterrows():

            result += (
                f"{row['invoice_number']} - "
                f"{row['client_name']} - "
                f"₹{row['balance_due']:,.2f}\n"
            )

        return result

    # 14. Average invoice amount
    elif (
        "average invoice" in question
        or "average invoice amount" in question
    ):

        average = df["total_amount"].mean()

        return f"The average invoice amount is ₹{average:,.2f}."

    # 15. Maximum invoice
    elif (
        "largest invoice" in question
        or "highest invoice" in question
        or "biggest invoice" in question
    ):

        invoice = df.loc[df["total_amount"].idxmax()]

        return (
            f"The largest invoice is {invoice['invoice_number']} "
            f"from {invoice['client_name']} "
            f"for ₹{invoice['total_amount']:,.2f}."
        )

    # 16. Minimum invoice
    elif (
        "smallest invoice" in question
        or "lowest invoice" in question
    ):

        invoice = df.loc[df["total_amount"].idxmin()]

        return (
            f"The smallest invoice is {invoice['invoice_number']} "
            f"from {invoice['client_name']} "
            f"for ₹{invoice['total_amount']:,.2f}."
        )

    # 17. Overall summary
    elif (
        "summary" in question
        or "overall" in question
        or "financial summary" in question
    ):

        total = df["total_amount"].sum()
        paid = df["paid_amount"].sum()
        outstanding = df["balance_due"].sum()

        pending = (df["status"] == "pending").sum()
        overdue = (df["status"] == "overdue").sum()

        return (
            f"Finance Summary:\n\n"
            f"Total invoices: {len(df)}\n"
            f"Total invoice amount: ₹{total:,.2f}\n"
            f"Total paid: ₹{paid:,.2f}\n"
            f"Total outstanding: ₹{outstanding:,.2f}\n"
            f"Pending invoices: {pending}\n"
            f"Overdue invoices: {overdue}"
        )

    # 18. Unknown question
    else:
        return (
            "Sorry, I don't understand that question yet. "
            "Try asking about invoices, clients, payments, "
            "outstanding amounts, pending invoices, or overdue invoices."
        )

if __name__ == "__main__":

    df = load_invoices()

    print("Invoices loaded:", len(df))

    while True:

        question = input("\nAsk a finance question (type 'exit' to stop): ")

        if question.lower() == "exit":
            break

        answer = ask_question(question, df)

        print("\nFinance Assistant:")
        print(answer)