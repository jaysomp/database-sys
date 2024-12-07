import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import xgboost as xgb
import os

def train_model(data_path='ufc-master.csv', output_file='predictions.txt'):
    with open(output_file, 'w') as f:
        def log(msg):
            print(msg)
            f.write(msg + '\n')
            
        if not os.path.exists(data_path):
            log("Error: Training data not found")
            return None
        
        df = pd.read_csv(data_path)
        df_prep = df.copy()
        
        df_prep['RedStance'] = df_prep['RedStance'].fillna('Unknown')
        df_prep['BlueStance'] = df_prep['BlueStance'].fillna('Unknown')
        
        for color in ['Red', 'Blue']:
            df_prep[f'{color}WinRate'] = np.where(
                df_prep[f'{color}Wins'] + df_prep[f'{color}Losses'] != 0,
                df_prep[f'{color}Wins'] / (df_prep[f'{color}Wins'] + df_prep[f'{color}Losses']),
                0
            )
        
        features = [
            'HeightDif', 'ReachDif', 'AgeDif', 'WinStreakDif', 'LoseStreakDif',
            'RedStance', 'BlueStance', 'RedWinRate', 'BlueWinRate',
            'RedAvgTDPct', 'BlueAvgTDPct'
        ]
        
        X = df_prep[features].copy()
        y = (df_prep['Winner'] == 'Red').astype(int)
        
        le = LabelEncoder()
        X['RedStance'] = le.fit_transform(X['RedStance'])
        X['BlueStance'] = le.fit_transform(X['BlueStance'])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = xgb.XGBClassifier(random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
        model.fit(X_train, y_train)
        
        log(f"Training accuracy: {model.score(X_train, y_train):.1%}")
        log(f"Test accuracy: {model.score(X_test, y_test):.1%}\n")
        
        return model, scaler, le, features

def predict_fights(model, scaler, le, features, pred_path='upcoming.csv', output_file='predictions.txt'):
    with open(output_file, 'a') as f:
        def log(msg):
            print(msg)
            f.write(msg + '\n')
            
        if not os.path.exists(pred_path):
            log("Error: Upcoming fights data not found")
            return
        
        df = pd.read_csv(pred_path)
        X_pred = df.copy()
        
        X_pred['RedStance'] = X_pred['RedStance'].fillna('Unknown')
        X_pred['BlueStance'] = X_pred['BlueStance'].fillna('Unknown')
        
        for color in ['Red', 'Blue']:
            X_pred[f'{color}WinRate'] = np.where(
                X_pred[f'{color}Wins'] + X_pred[f'{color}Losses'] != 0,
                X_pred[f'{color}Wins'] / (X_pred[f'{color}Wins'] + X_pred[f'{color}Losses']),
                0
            )
        
        X_pred = X_pred[features].copy()
        X_pred['RedStance'] = le.transform(X_pred['RedStance'])
        X_pred['BlueStance'] = le.transform(X_pred['BlueStance'])
        X_pred_scaled = scaler.transform(X_pred)
        

        probs = model.predict_proba(X_pred_scaled)
        preds = model.predict(X_pred_scaled)
        
        for weight_class in sorted(df['WeightClass'].unique()):
            mask = df['WeightClass'] == weight_class
            log(f"\n{weight_class}")
            log("-" * 50)
            
            for i, row in df[mask].iterrows():
                winner = row['RedFighter'] if preds[i] == 1 else row['BlueFighter']
                red_prob, blue_prob = probs[i][1], probs[i][0]
                log(f"{row['RedFighter']} vs {row['BlueFighter']}")
                log(f"Winner: {winner} ({max(red_prob, blue_prob):.0%} confident)\n")

if __name__ == "__main__":
    model, scaler, le, features = train_model()
    if model:
        predict_fights(model, scaler, le, features)