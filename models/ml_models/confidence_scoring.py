import numpy as np

class ConfidenceScorer:
    def __init__(self, clf_model=None, reg_model=None):
        self.clf_model = clf_model
        self.reg_model = reg_model

    def calculate_classification_confidence(self, X_transformed):
        """Calculates confidence for fertilizer type prediction using probabilities."""
        if self.clf_model and hasattr(self.clf_model, 'predict_proba'):
            probs = self.clf_model.predict_proba(X_transformed)
            max_prob = np.max(probs, axis=1)
            return max_prob * 100
        return np.array([0.0])

    def calculate_regression_confidence(self, model, X_transformed, y_pred):
        """
        Estimates quantity confidence based on ensemble variance.
        Higher variance across trees in Random Forest = Lower confidence.
        """
        if hasattr(model, 'estimators_'): # Random Forest
            all_tree_preds = np.array([tree.predict(X_transformed) for tree in model.estimators_])
            std_dev = np.std(all_tree_preds, axis=0)
            
            # Normalize confidence: 100 - (CV * 100) where CV is Coefficient of Variation
            # Cap at 0-100%
            cv = std_dev / (y_pred + 1e-6)
            confidence = np.maximum(0, 100 - (cv * 100))
            return confidence
        
        # Default fallback for models without ensemble (e.g. XGBoost/Linear)
        # We can use a heuristic or distance-based approach later
        return np.array([85.0] * len(y_pred))

    def get_confidence_level(self, score):
        """Categorizes confidence score into High, Medium, or Low."""
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        else:
            return "Low"

    def combine_confidence(self, type_conf, quant_conf, weights=(0.6, 0.4)):
        """Combines type and quantity confidence into an overall score."""
        overall = (type_conf * weights[0]) + (quant_conf * weights[1])
        return overall

if __name__ == "__main__":
    print("ConfidenceScorer module initialized.")
