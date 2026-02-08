from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.svm import SVC, SVR
import joblib
import os

class HyperparameterTuner:
    def __init__(self, mode='classification'):
        self.mode = mode
        self.best_params = {}
        self.best_models = {}

    def tune_random_forest(self, X_train, y_train):
        """Performs search for Random Forest."""
        print(f"Tuning Random Forest ({self.mode})...")
        if self.mode == 'classification':
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5],
                'max_features': ['sqrt', 'log2']
            }
            rf = RandomForestClassifier(random_state=42)
        else: # regression
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            rf = RandomForestRegressor(random_state=42)
            
        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, 
                                   cv=3, n_jobs=-1, verbose=1, 
                                   scoring='accuracy' if self.mode == 'classification' else 'r2')
        grid_search.fit(X_train, y_train)
        
        self.best_params['RandomForest'] = grid_search.best_params_
        self.best_models['RandomForest'] = grid_search.best_estimator_
        print(f"Best RF Params: {grid_search.best_params_}")
        return grid_search.best_estimator_

    def tune_xgboost(self, X_train, y_train):
        """Performs search for XGBoost."""
        print(f"Tuning XGBoost ({self.mode})...")
        if self.mode == 'classification':
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 1.0]
            }
            xgb = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
        else: # regression
            param_dist = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
            xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
            
        random_search = RandomizedSearchCV(estimator=xgb, param_distributions=param_dist, 
                                          n_iter=10, cv=3, n_jobs=-1, verbose=1, 
                                          scoring='accuracy' if self.mode == 'classification' else 'r2', 
                                          random_state=42)
        random_search.fit(X_train, y_train)
        
        self.best_params['XGBoost'] = random_search.best_params_
        self.best_models['XGBoost'] = random_search.best_estimator_
        print(f"Best XGBoost Params: {random_search.best_params_}")
        return random_search.best_estimator_

    def save_best_model(self, model_name, version='v1.0.0', path=None):
        """Saves the best tuned model."""
        if path is None:
            path = f'models/{version}/best_{self.mode}_{model_name.lower()}_tuned.pkl'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.best_models[model_name], path)
        print(f"Best tuned {self.mode} {model_name} saved to {path}")

if __name__ == "__main__":
    print("HyperparameterTuner module initialized.")
