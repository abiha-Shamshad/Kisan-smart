import time
from concurrent.futures import ThreadPoolExecutor
from models.ml_models.inference_engine import InferenceEngine
import numpy as np


def benchmark_inference(num_requests=100, max_workers=10):
    engine = InferenceEngine()

    sample = {
        "Nitrogen": 40,
        "Phosphorus": 50,
        "Potassium": 30,
        "pH": 6.5,
        "Moisture": 45.0,
        "Temperature": 28.0,
        "Crop_Type": "Wheat",
        "Growth_Stage": "Vegetative",
        "Farm_Area": 2.5,
    }

    print(f"--- Benchmarking {num_requests} requests with {max_workers} workers ---")

    latencies = []

    def single_test():
        start = time.time()
        engine.predict(sample)
        return (time.time() - start) * 1000

    start_total = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda _: single_test(), range(num_requests)))
    end_total = time.time()

    total_time = end_total - start_total
    avg_latency = np.mean(results)
    p95_latency = np.percentile(results, 95)
    p99_latency = np.percentile(results, 99)
    throughput = num_requests / total_time

    print(f"\nResults:")
    print(f"Total Time: {total_time:.2f} s")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"P95 Latency: {p95_latency:.2f} ms")
    print(f"P99 Latency: {p99_latency:.2f} ms")
    print(f"Throughput: {throughput:.2f} req/s")

    if avg_latency < 3000:
        print("\nSUCCESS: Inference time is well below 3 seconds.")
    else:
        print("\nFAILURE: Inference target not met.")


if __name__ == "__main__":
    benchmark_inference()
