import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

data = pd.read_csv("dataset.csv")

# Expense Categorization
vectorizer = TfidfVectorizer()
X_text = vectorizer.fit_transform(data["description"])

rf = RandomForestClassifier()
rf.fit(X_text, data["category"])

joblib.dump((rf,vectorizer),"models/category_model.pkl")

# Spending clusters
kmeans = KMeans(n_clusters=4)
kmeans.fit(data[["amount"]])

joblib.dump(kmeans,"models/cluster_model.pkl")

# Expense prediction
X = data[["month"]]
y = data["amount"]

lr = LinearRegression()
lr.fit(X,y)

joblib.dump(lr,"models/regression_model.pkl")

# Fraud detection
iso = IsolationForest()

iso.fit(data[["amount"]])

joblib.dump(iso,"models/anomaly_model.pkl")

print("Models trained")