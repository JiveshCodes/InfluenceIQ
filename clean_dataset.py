import pandas as pd
import os

def clean_csv():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, 'dataset.csv')
    
    if not os.path.exists(csv_path):
        print("CSV not found.")
        return

    print(f"Cleaning {csv_path}...")
    
    # Load with low_memory=False to handle mixed types
    df = pd.read_csv(csv_path, low_memory=False)
    
    # 1. Remove duplicate names (keep latest)
    initial_count = len(df)
    df = df.drop_duplicates(subset=['name'], keep='last')
    
    # 2. Fix numeric columns
    numeric_cols = ['followers', 'engagement_rate', 'avg_likes', 'avg_comments', 'price_usd', 'fraud_risk']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # 3. Fix categorical columns
    df['category'] = df['category'].fillna('Tech')
    df['subcategory'] = df['subcategory'].fillna('General')
    df['platform'] = df['platform'].fillna('YouTube')
    df['gender'] = df['gender'].fillna('Unknown')
    df['location'] = df['location'].fillna('Global')
    df['verified'] = df['verified'].map(lambda x: str(x).lower() == 'true')
    
    # 4. Strip whitespace from strings
    for col in df.select_dtypes(['object']).columns:
        df[col] = df[col].astype(str).str.strip()

    # 5. Reset IDs to be sequential
    df = df.sort_values('id')
    df['id'] = range(1, len(df) + 1)
    
    # Save cleaned version
    df.to_csv(csv_path, index=False)
    
    print(f"Cleanup Complete!")
    print(f"Removed {initial_count - len(df)} duplicates.")
    print(f"Total influencers now: {len(df)}")

if __name__ == "__main__":
    clean_csv()
