import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
import pandas as pd
import numpy as np
import os

class ModelEvaluator:
    def __init__(self, output_dir='results/visualizations'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_confusion_matrix(self, y_true, y_pred, model_name, labels):
        """Plots and saves a confusion matrix heatmap."""
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/{model_name.lower()}_cm.png')
        plt.close()
        print(f"Confusion matrix for {model_name} saved.")

    def save_report(self, y_true, y_pred, model_name, mode='classification'):
        """Saves classification report or regression metrics to a text file."""
        report_dir = 'results/evaluation_reports'
        os.makedirs(report_dir, exist_ok=True)
        report_path = f'{report_dir}/{model_name.lower()}_report.txt'
        
        with open(report_path, 'w') as f:
            if mode == 'classification':
                report = classification_report(y_true, y_pred)
                f.write(report)
            else: # regression
                from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
                r2 = r2_score(y_true, y_pred)
                mae = mean_absolute_error(y_true, y_pred)
                rmse = np.sqrt(mean_squared_error(y_true, y_pred))
                f.write(f"R2 Score: {r2:.4f}\n")
                f.write(f"Mean Absolute Error: {mae:.4f}\n")
                f.write(f"Root Mean Squared Error: {rmse:.4f}\n")
                
        print(f"Evaluation report for {model_name} saved to {report_path}")

    def plot_feature_importance(self, model, feature_names, model_name):
        """Plots feature importance for tree-based models."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            # Select top 15 features
            top_indices = indices[:15]
            top_importances = importances[top_indices]
            top_names = [feature_names[i] for i in top_indices]

            plt.figure(figsize=(12, 8))
            plt.barh(range(len(top_importances)), top_importances[::-1], align='center')
            plt.yticks(range(len(top_importances)), top_names[::-1])
            plt.xlabel('Importance Score')
            plt.title(f'Top 15 Feature Importances - {model_name}')
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/{model_name.lower()}_feature_importance.png')
            plt.close()
            print(f"Feature importance plot for {model_name} saved.")
        else:
            print(f"Model {model_name} does not support feature_importances_.")

    def plot_roc_curve(self, model, X_test, y_test, model_name, labels):
        """Plots Multi-class ROC curve using One-vs-Rest approach."""
        from sklearn.preprocessing import label_binarize
        from sklearn.metrics import roc_curve, auc
        
        y_test_bin = label_binarize(y_test, classes=labels)
        n_classes = len(labels)
        
        y_score = model.predict_proba(X_test)
        
        plt.figure(figsize=(10, 8))
        for i in range(n_classes):
            fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, label=f'Class {labels[i]} (AUC = {roc_auc:0.2f})')
            
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'Multi-class ROC - {model_name}')
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/{model_name.lower()}_roc.png')
        plt.close()
        print(f"ROC curve for {model_name} saved.")

    def plot_learning_curve(self, estimator, X, y, model_name):
        """Plots the learning curve for a model."""
        from sklearn.model_selection import learning_curve
        
        train_sizes, train_scores, test_scores = learning_curve(
            estimator, X, y, cv=5, n_jobs=-1, 
            train_sizes=np.linspace(.1, 1.0, 5)
        )
        
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)
        
        plt.figure(figsize=(10, 6))
        plt.grid()
        plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                         train_scores_mean + train_scores_std, alpha=0.1, color="r")
        plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                         test_scores_mean + test_scores_std, alpha=0.1, color="g")
        plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
        plt.plot(train_sizes, test_scores_mean, 'o-', color="g", label="Cross-validation score")
        plt.xlabel("Training examples")
        plt.ylabel("Score")
        plt.title(f"Learning Curve - {model_name}")
        plt.legend(loc="best")
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/{model_name.lower()}_learning_curve.png')
        plt.close()
        print(f"Learning curve for {model_name} saved.")

    def plot_regression_results(self, y_true, y_pred, model_name):
        """Plots Actual vs Predicted for regression."""
        plt.figure(figsize=(10, 6))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        plt.xlabel('Actual Quantity')
        plt.ylabel('Predicted Quantity')
        plt.title(f'Actual vs Predicted - {model_name}')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/{model_name.lower()}_actual_vs_pred.png')
        plt.close()
        print(f"Regression plot for {model_name} saved.")

    def plot_residuals(self, y_true, y_pred, model_name):
        """Plots residuals for regression."""
        residuals = y_true - y_pred
        plt.figure(figsize=(10, 6))
        plt.scatter(y_pred, residuals, alpha=0.5)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Predicted Quantity')
        plt.ylabel('Residuals')
        plt.title(f'Residual Plot - {model_name}')
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/{model_name.lower()}_residuals.png')
        plt.close()
        print(f"Residual plot for {model_name} saved.")

if __name__ == "__main__":
    print("ModelEvaluator module initialized.")
