from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# API URL
API_URL = "https://www.tekika.io/api/nft/nft-xp?pwd=VZSnM2as9wKwqeE"

# Updated Date Ranges for Months
MONTH_1_START = datetime.date(2025, 1, 24)
MONTH_1_END = datetime.date(2025, 2, 23)
MONTH_2_START = datetime.date(2025, 2, 24)
MONTH_2_END = datetime.date(2025, 3, 23)
MONTH_3_START = datetime.date(2025, 3, 24)
MONTH_3_END = datetime.date(2025, 4, 24)

def fetch_data():
    """Fetch total Tekika XP and mints from the API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return None

def count_mints_in_period(data, start_date, end_date):
    """Count mints that occurred within a specific date range."""
    count = 0
    for item in data:
        mint_date_str = item.get("mintDate")
        if mint_date_str:
            mint_date = datetime.datetime.strptime(mint_date_str, "%Y-%m-%d").date()
            if start_date <= mint_date <= end_date:
                count += 1
    return count

def determine_month():
    """Automatically determine the current month based on the date."""
    today = datetime.date.today()
    if MONTH_1_START <= today <= MONTH_1_END:
        return 1
    elif MONTH_2_START <= today <= MONTH_2_END:
        return 2
    elif MONTH_3_START <= today <= MONTH_3_END:
        return 3
    else:
        return None  # Outside valid date range

def calculate_reward(user_xp, data, month):
    """Calculate the reward based on newly added mints per month."""
    if data is None or user_xp <= 0:
        return None

    # Total mints per month (automatically counted)
    month_1_mints = count_mints_in_period(data, MONTH_1_START, MONTH_1_END)
    month_2_mints = count_mints_in_period(data, MONTH_2_START, MONTH_2_END)
    month_3_mints = count_mints_in_period(data, MONTH_3_START, MONTH_3_END)

    # Determine new mints added per month
    if month == 1:
        new_users = month_1_mints
        pool = (new_users * 8) / 3  # Month 1 pool is divided by 3
        carry_over = pool  # One-third is carried to Month 2 & 3

    elif month == 2:
        new_users = max(month_2_mints - month_1_mints, 0)  # Only count new mints
        pool = (new_users * 8) / 2  # Month 2 pool is divided by 2
        carry_over = (month_1_mints * 8) / 3  # One-third from Month 1 carried over
        pool += carry_over  # Add Month 1 carry-over

    elif month == 3:
        new_users = max(month_3_mints - month_2_mints, 0)  # Only count new mints
        pool = (new_users * 8)  # Month 3 gets new users' contribution
        carry_over_1 = (month_1_mints * 8) / 3  # One-third from Month 1 carried over
        carry_over_2 = ((month_2_mints - month_1_mints) * 8) / 2  # Half from Month 2 carried over
        pool += carry_over_1 + carry_over_2  # Month 3 gets both carry-overs

    else:
        return None  # Invalid month selection

    # Calculate total XP across all minted Tekika NFTs
    total_xp = sum(int(item.get("XP", 0)) for item in data)

    # Calculate reward for user XP
    reward = (user_xp / total_xp) * pool if total_xp > 0 else 0
    return round(reward, 2), month_1_mints, new_users

@app.route("/reward", methods=["GET"])
def get_reward():
    """API endpoint to return the reward for any XP amount."""
    user_xp = request.args.get("xp", type=int, default=100000)  # Default to 100,000 XP
    month = determine_month()

    if month is None:
        return jsonify({"error": "Outside the valid date range for rewards"}), 400

    data = fetch_data()
    reward, month_1_mints, current_month_mints = calculate_reward(user_xp, data, month)

    if reward is None:
        return jsonify({"error": "Invalid request or failed to fetch data"}), 400

    return jsonify({
        "xp": user_xp,
        "month": month,
        "reward": reward,
        "month_1_mints": month_1_mints,
        "current_month_mints": current_month_mints,
        "message": f"Today's reward for {user_xp} XP in Month {month} is ${reward}\n"
                   f"Total mints in Month 1: {month_1_mints}\n"
                   f"Total mints in current month: {current_month_mints}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
