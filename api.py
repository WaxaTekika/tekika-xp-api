from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# API URL
API_URL = "https://www.tekika.io/api/nft/nft-xp?pwd=VZSnM2as9wKwqeE"

# Date Ranges for Months
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

        total_season2_tekika = sum(1 for item in data if item.get("seasonIndex") == 2)
        total_xp = sum(int(item.get("XP", 0)) for item in data)

        return total_season2_tekika, total_xp
    except Exception as e:
        return None, None

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

def calculate_reward(user_xp, total_season2_tekika, total_xp, month):
    """Calculate the reward based on the detected month."""
    if total_season2_tekika is None or total_xp is None or user_xp <= 0:
        return None

    # Base pool calculation
    pool = 0
    if total_season2_tekika <= 10000:
        pool += total_season2_tekika * 8
    elif total_season2_tekika <= 20000:
        pool += (10000 * 8) + ((total_season2_tekika - 10000) * 6)
    else:
        pool += (10000 * 8) + (10000 * 6) + ((total_season2_tekika - 20000) * 5)

    # Carry-over logic for each month
    if month == 1:
        pool /= 3  # Month 1 pool is divided by 3
        month_1_share = pool  # One-third is carried to Month 2 & 3

    elif month == 2:
        month_1_share = (pool / 3)  # One-third from Month 1 carried over
        pool = (pool / 2) + month_1_share  # Month 2 pool is divided by 2, adding Month 1 carry-over

    elif month == 3:
        month_1_share = (pool / 3)  # One-third from Month 1 carried over
        month_2_share = (pool / 2)  # Half from Month 2 carried over
        pool = month_1_share + month_2_share  # Month 3 gets both carry-overs

    else:
        return None  # Invalid month selection

    # Calculate reward for user XP
    reward = (user_xp / total_xp) * pool if total_xp > 0 else 0
    return round(reward, 2)

@app.route("/reward", methods=["GET"])
def get_reward():
    """API endpoint to return the reward for any XP amount."""
    user_xp = request.args.get("xp", type=int, default=100000)  # Default to 100,000 XP
    month = determine_month()

    if month is None:
        return jsonify({"error": "Outside the valid date range for rewards"}), 400

    total_season2_tekika, total_xp = fetch_data()
    reward = calculate_reward(user_xp, total_season2_tekika, total_xp, month)

    if reward is None:
        return jsonify({"error": "Invalid request or failed to fetch data"}), 400

    return jsonify({
        "xp": user_xp,
        "month": month,
        "reward": reward,
        "message": f"Today's reward for {user_xp} XP in Month {month} is ${reward}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
