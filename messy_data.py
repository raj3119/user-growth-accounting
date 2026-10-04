# Create a test script: make_different_data.py
import pandas as pd
import random
import uuid

# Create a small 10-week dataset with explosive growth
data = {}
base_users = [str(uuid.uuid4())[:16] for _ in range(500)]

for week_num in range(1, 11):
    col = f"w{week_num}"
    # Users grow rapidly week over week
    num_users = 500 + (week_num * 300)
    weekly_active = random.sample(base_users, k=min(len(base_users), int(num_users * 0.7)))
    new_users = [str(uuid.uuid4())[:16] for _ in range(num_users - len(weekly_active))]
    base_users.extend(new_users)
    data[col] = pd.Series(weekly_active + new_users)

df_diff = pd.DataFrame(data)
df_diff.to_excel("Different_Company_Test.xlsx", index=False)
print("SUCCESS: Created Different_Company_Test.xlsx")