import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error

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

class MLEngineModels:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.base_dir, 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.classifier = None
        self.scaler_cls = None
        self.le_niche = None
        
        self.regressor = None
        self.scaler_reg = None
        self.le_gender = None
        
        self.knn = None
        self.scaler_knn = None
        self.le_cat = None
        self.le_sub = None

    def _train_and_save(self, df):
        print("[ML Models] Training new Scikit-Learn models...")
        # Deep copy to avoid warnings
        data = df.copy()
        
        for col in ['followers', 'engagement_rate', 'avg_likes', 'avg_comments']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            
        data['niche'] = data['category'] + " " + data['subcategory']
        
        # 1. Classification (Nano/Micro/Macro/Mega)
        data['influencer_tier'] = data['followers'].apply(categorize_influencer)
        self.le_niche = LabelEncoder()
        data['niche_encoded'] = self.le_niche.fit_transform(data['niche'])
        
        self.le_gender = LabelEncoder()
        # Handle cases where gender might not exist yet
        if 'gender' not in data.columns:
            data['gender'] = 'Unknown'
        data['gender_enc'] = self.le_gender.fit_transform(data['gender'])
        
        X_cls = data[['followers', 'engagement_rate', 'niche_encoded', 'avg_likes', 'avg_comments', 'gender_enc']]
        y_cls = data['influencer_tier']
        
        self.scaler_cls = StandardScaler()
        X_cls_scaled = self.scaler_cls.fit_transform(X_cls)
        
        self.classifier = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
        self.classifier.fit(X_cls_scaled, y_cls)
        
        # 2. Regression (Predict Engagement Rate)
        X_reg = data[['followers', 'avg_likes', 'avg_comments', 'niche_encoded', 'gender_enc']]
        y_reg = data['engagement_rate']
        
        self.scaler_reg = StandardScaler()
        X_reg_scaled = self.scaler_reg.fit_transform(X_reg)
        
        self.regressor = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        self.regressor.fit(X_reg_scaled, y_reg)
        
        # 3. Recommendation (KNN)
        self.le_cat = LabelEncoder()
        self.le_sub = LabelEncoder()
        data['cat_enc'] = self.le_cat.fit_transform(data['category'])
        data['sub_enc'] = self.le_sub.fit_transform(data['subcategory'])
        
        X_knn = data[['followers', 'engagement_rate', 'cat_enc', 'sub_enc', 'avg_likes', 'avg_comments', 'gender_enc']]
        self.scaler_knn = StandardScaler()
        X_knn_scaled = self.scaler_knn.fit_transform(X_knn)
        
        self.knn = NearestNeighbors(n_neighbors=6, metric='cosine')
        self.knn.fit(X_knn_scaled)
        
        # Save models
        joblib.dump(self.classifier, os.path.join(self.models_dir, 'classifier.pkl'))
        joblib.dump(self.scaler_cls, os.path.join(self.models_dir, 'scaler_cls.pkl'))
        joblib.dump(self.le_niche, os.path.join(self.models_dir, 'le_niche.pkl'))
        joblib.dump(self.le_gender, os.path.join(self.models_dir, 'le_gender.pkl'))
        
        joblib.dump(self.regressor, os.path.join(self.models_dir, 'regressor.pkl'))
        joblib.dump(self.scaler_reg, os.path.join(self.models_dir, 'scaler_reg.pkl'))
        
        joblib.dump(self.knn, os.path.join(self.models_dir, 'knn.pkl'))
        joblib.dump(self.scaler_knn, os.path.join(self.models_dir, 'scaler_knn.pkl'))
        joblib.dump(self.le_cat, os.path.join(self.models_dir, 'le_cat.pkl'))
        joblib.dump(self.le_sub, os.path.join(self.models_dir, 'le_sub.pkl'))
        
        print("[ML Models] Training complete and models saved.")

    def load_or_train(self, df):
        req_files = ['classifier.pkl', 'scaler_cls.pkl', 'le_niche.pkl', 'le_gender.pkl',
                     'regressor.pkl', 'scaler_reg.pkl', 
                     'knn.pkl', 'scaler_knn.pkl', 'le_cat.pkl', 'le_sub.pkl']
        
        needs_training = False
        for f in req_files:
            if not os.path.exists(os.path.join(self.models_dir, f)):
                needs_training = True
                break
                
        if needs_training:
            self._train_and_save(df)
        else:
            print("[ML Models] Loading pre-trained models...")
            self.classifier = joblib.load(os.path.join(self.models_dir, 'classifier.pkl'))
            self.scaler_cls = joblib.load(os.path.join(self.models_dir, 'scaler_cls.pkl'))
            self.le_niche = joblib.load(os.path.join(self.models_dir, 'le_niche.pkl'))
            self.le_gender = joblib.load(os.path.join(self.models_dir, 'le_gender.pkl'))
            
            self.regressor = joblib.load(os.path.join(self.models_dir, 'regressor.pkl'))
            self.scaler_reg = joblib.load(os.path.join(self.models_dir, 'scaler_reg.pkl'))
            
            self.knn = joblib.load(os.path.join(self.models_dir, 'knn.pkl'))
            self.scaler_knn = joblib.load(os.path.join(self.models_dir, 'scaler_knn.pkl'))
            self.le_cat = joblib.load(os.path.join(self.models_dir, 'le_cat.pkl'))
            self.le_sub = joblib.load(os.path.join(self.models_dir, 'le_sub.pkl'))
            print("[ML Models] Loaded successfully.")

    def predict_classification(self, followers, engagement_rate, category, subcategory, avg_likes, avg_comments, gender='Unknown'):
        niche = f"{category} {subcategory}"
        try:
            niche_enc = self.le_niche.transform([niche])[0]
        except:
            niche_enc = 0
            
        try:
            gender_enc = self.le_gender.transform([gender])[0]
        except:
            gender_enc = 0
            
        X = [[followers, engagement_rate, niche_enc, avg_likes, avg_comments, gender_enc]]
        X_scaled = self.scaler_cls.transform(X)
        pred = self.classifier.predict(X_scaled)[0]
        
        # Calculate confidence
        probs = self.classifier.predict_proba(X_scaled)[0]
        confidence = max(probs) * 100
        return str(pred), float(confidence)

    def predict_engagement(self, followers, category, subcategory, avg_likes, avg_comments, gender='Unknown'):
        niche = f"{category} {subcategory}"
        try:
            niche_enc = self.le_niche.transform([niche])[0]
        except:
            niche_enc = 0
            
        try:
            gender_enc = self.le_gender.transform([gender])[0]
        except:
            gender_enc = 0
            
        X = [[followers, avg_likes, avg_comments, niche_enc, gender_enc]]
        X_scaled = self.scaler_reg.transform(X)
        pred = self.regressor.predict(X_scaled)[0]
        return float(max(0.1, round(pred, 2)))

    def recommend_similar(self, df, influencer_name, top_n=3):
        # Find the influencer
        inf = df[df['name'].str.lower() == influencer_name.lower()]
        if inf.empty:
            return []
            
        inf = inf.iloc[0]
        
        try:
            cat_enc = self.le_cat.transform([inf['category']])[0]
            sub_enc = self.le_sub.transform([inf['subcategory']])[0]
        except:
            cat_enc = 0
            sub_enc = 0
            
        try:
            gender_enc = self.le_gender.transform([inf.get('gender', 'Unknown')])[0]
        except:
            gender_enc = 0
            
        X = [[inf['followers'], inf['engagement_rate'], cat_enc, sub_enc, inf['avg_likes'], inf['avg_comments'], gender_enc]]
        X_scaled = self.scaler_knn.transform(X)
        
        distances, indices = self.knn.kneighbors(X_scaled, n_neighbors=top_n + 1)
        
        similar_influencers = []
        for i in range(1, len(indices[0])):  # skip 0 as it's the influencer itself
            idx = indices[0][i]
            sim_inf = df.iloc[idx]
            dist = distances[0][i]
            sim_score = round((1 - dist) * 100, 1) # Cosine similarity percentage
            similar_influencers.append({
                'name': str(sim_inf['name']),
                'platform': str(sim_inf['platform']),
                'category': str(sim_inf['category']),
                'followers': int(sim_inf['followers']),
                'similarity_score': float(sim_score)
            })
            
        return similar_influencers
