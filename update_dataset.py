import pandas as pd
import os
import random

# Common name endings or simple rules to guess gender reasonably well
def guess_gender(name):
    first_name = name.split()[0].lower()
    # Many female names in India end with a, i, ee, or y.
    if first_name.endswith('a') or first_name.endswith('i') or first_name.endswith('ee') or first_name.endswith('y'):
        return 'Female'
    else:
        return 'Male'

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'dataset.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return
        
    df = pd.read_csv(csv_path)
    
    # If gender already exists, don't overwrite it
    if 'gender' not in df.columns:
        print("Adding 'gender' column...")
        # Use our simple heuristic, with a few manual overrides just in case
        df['gender'] = df['name'].apply(guess_gender)
        
        # Save back to CSV
        df.to_csv(csv_path, index=False)
        print("Successfully updated dataset.csv with 'gender' column!")
    else:
        print("'gender' column already exists in dataset.csv.")
        
if __name__ == "__main__":
    main()
