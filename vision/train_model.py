import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. Load Data
try:
    data = pd.read_csv("hand_data.csv")
except FileNotFoundError:
    print("Error: hand_data.csv not found. Run capture_data.py first!")
    exit()

X = data.iloc[:, 1:].values # Features (Coordinates)
y = data.iloc[:, 0].values  # Labels

# 2. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

# 3. Train Random Forest (Fast & Robust)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 4. Evaluate
y_pred = model.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")

# 5. Save
with open('model.p', 'wb') as f:
    pickle.dump(model, f)

print("Model saved to model.p successfully!")