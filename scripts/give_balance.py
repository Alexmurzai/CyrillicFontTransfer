import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.users_db import get_user_by_email, add_balance, set_subscription

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python scripts/give_balance.py <email> balance <amount>")
        print("  python scripts/give_balance.py <email> subscription <days>")
        print("\nExamples:")
        print("  python scripts/give_balance.py alex@example.com balance 1000")
        print("  python scripts/give_balance.py alex@example.com subscription 365")
        return

    email = sys.argv[1]
    mode = sys.argv[2].lower()
    value = int(sys.argv[3])

    user = get_user_by_email(email)
    if not user:
        print(f"Error: User with email '{email}' not found in database.")
        return

    user_id = user["id"]

    if mode == "balance":
        add_balance(user_id, value)
        print(f"Successfully added {value} generations to {email}.")
        print(f"New balance: {user['balance'] + value}")
    elif mode == "subscription":
        # Give subscription
        end_date = datetime.utcnow() + timedelta(days=value)
        set_subscription(user_id, end_date)
        print(f"Successfully granted subscription to {email} for {value} days (until {end_date.strftime('%Y-%m-%d %H:%M:%S')} UTC).")
    else:
        print(f"Unknown mode: {mode}. Use 'balance' or 'subscription'.")

if __name__ == "__main__":
    main()
