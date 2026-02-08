from models.ml_models.inference_engine import InferenceEngine
import threading

class MLModelService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MLModelService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        print("Initializing MLModelService (Singleton)...")
        self.engine = InferenceEngine(version='v1.0.0')
        self._initialized = True

    def predict(self, data):
        """Standardized prediction gateway."""
        return self.engine.predict(data)

# Singleton access
ml_service = MLModelService()
