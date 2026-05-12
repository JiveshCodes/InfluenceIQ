import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score

def categorize_influencer(followers):
    f = float(followers)
    if f >= 1000000:
        return 'Mega Influencer'
    elif f >= 500000:
        return 'Macro Influencer'
    elif f >= 50000:
        return 'Micro Influencer'
    else:
        return 'Nano Influencer'

def train_all():
    base = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(base, 'dataset.csv'))

    # Clean numeric columns
    for col in ['followers', 'engagement_rate', 'avg_likes', 'avg_comments']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['niche'] = df['category'] + " " + df['subcategory']

    print("--- Training ML Models ---")
    
    # 1. Influencer Classification Model (Random Forest Classifier)
    print("\n1. Training Classification Model (Nano/Micro/Macro/Mega)")
    df['influencer_tier'] = df['followers'].apply(categorize_influencer)
    
    # Features for classification
    le_niche = LabelEncoder()
    df['niche_encoded'] = le_niche.fit_transform(df['niche'])
    
    X_cls = df[['followers', 'engagement_rate', 'niche_encoded', 'avg_likes', 'avg_comments']]
    y_cls = df['influencer_tier']
    
    X_train, X_test, y_train, y_test = train_test_split(X_cls, y_cls, test_size=0.2, random_state=42)
    
    scaler_cls = StandardScaler()
    X_train_scaled = scaler_cls.fit_transform(X_train)
    X_test_scaled = scaler_cls.transform(X_test)
    
    rf_cls = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
    rf_cls.fit(X_train_scaled, y_train)
    
    y_pred = rf_cls.predict(X_test_scaled)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    # 2. Engagement Prediction System (Random Forest Regressor)
    print("\n2. Training Engagement Prediction Model (Regressor)")
    # We predict engagement rate based on followers, avg_likes, avg_comments, niche
    X_reg = df[['followers', 'avg_likes', 'avg_comments', 'niche_encoded']]
    y_reg = df['engagement_rate']
    
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
    
    scaler_reg = StandardScaler()
    X_train_r_scaled = scaler_reg.fit_transform(X_train_r)
    X_test_r_scaled = scaler_reg.transform(X_test_r)
    
    rf_reg = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
    rf_reg.fit(X_train_r_scaled, y_train_r)
    
    y_pred_r = rf_reg.predict(X_test_r_scaled)
    print(f"MSE: {mean_squared_error(y_test_r, y_pred_r):.4f}")
    print(f"R2 Score: {r2_score(y_test_r, y_pred_r):.4f}")

    # 3. Recommendation System (KNN)
    print("\n3. Training Influencer Recommendation Model (KNN)")
    # Features: followers, engagement_rate, category encoded, subcategory encoded
    le_cat = LabelEncoder()
    le_sub = LabelEncoder()
    df['cat_enc'] = le_cat.fit_transform(df['category'])
    df['sub_enc'] = le_sub.fit_transform(df['subcategory'])
    
    X_knn = df[['followers', 'engagement_rate', 'cat_enc', 'sub_enc', 'avg_likes', 'avg_comments']]
    scaler_knn = StandardScaler()
    X_knn_scaled = scaler_knn.fit_transform(X_knn)
    
    knn = NearestNeighbors(n_neighbors=6, metric='cosine')
    knn.fit(X_knn_scaled)
    print("KNN model fitted successfully.")
    
    # Save models and preprocessors
    models_dir = os.path.join(base, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    joblib.dump(rf_cls, os.path.join(models_dir, 'classifier.pkl'))
    joblib.dump(scaler_cls, os.path.join(models_dir, 'scaler_cls.pkl'))
    joblib.dump(le_niche, os.path.join(models_dir, 'le_niche.pkl'))
    
    joblib.dump(rf_reg, os.path.join(models_dir, 'regressor.pkl'))
    joblib.dump(scaler_reg, os.path.join(models_dir, 'scaler_reg.pkl'))
    
    joblib.dump(knn, os.path.join(models_dir, 'knn.pkl'))
    joblib.dump(scaler_knn, os.path.join(models_dir, 'scaler_knn.pkl'))
    joblib.dump(le_cat, os.path.join(models_dir, 'le_cat.pkl'))
    joblib.dump(le_sub, os.path.join(models_dir, 'le_sub.pkl'))
    
    print("\nModels saved to /models directory successfully.")

if __name__ == '__main__':
    train_all()
