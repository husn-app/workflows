"""
Example Commands:
python compute_similar_products_cache.py --run=benchmark for benchmarking against batch sizes.
python compute_similar_products_cache.py --run=full saves cache of 128 similar products in similar_products_cache.npy

This pipeline takes ~30 mins to run on Macbook. 
Requirements : pip install torch==2.4.0 torchvision==0.19.0 numpy==1.26.4 faiss-cpu==1.7.4

Output:
1. similar_products_cache.pt : ~500KB/product -> 700MB / 1.5M product. 
"""

import time
import os
import argparse
import faiss
import torch

from tqdm import tqdm
import numpy as np
torch.set_grad_enabled(False)

NUM_NEIGHBOURS = 128


def compute_similar_products_cache(index, image_embeddings):
    batch_size = 1024
    N, DIM = image_embeddings.shape
    similar_products_cache = np.zeros((N, NUM_NEIGHBOURS), dtype=np.int32)

    print(f'N = {N} | DIM = {DIM} | Batch Size = {batch_size} | Cached Neighbors : {NUM_NEIGHBOURS}')

    for batch_start in tqdm(range(0, N, batch_size)):
        _, indexes = index.search(image_embeddings[batch_start:batch_start + batch_size].detach().numpy(),  NUM_NEIGHBOURS) 
        similar_products_cache[batch_start:batch_start + batch_size] = indexes
    return similar_products_cache

def benchmark(index, image_embeddings):
    for i in range(1, 10 + 1): # 2 -> 1024
        batch_size = 2**i
        total_time = 0
        num_runs = 10
        
        for _ in range(num_runs):
            start_time = time.perf_counter()
            similarities, indexes = index.search(image_embeddings[:batch_size].detach().numpy(), 100)
            end_time = time.perf_counter()
            total_time += end_time - start_time
        
        avg_time = total_time / num_runs
        latency_per_vector = avg_time / batch_size
        
        print(f"Batch size: {batch_size}, Latency per vector: {latency_per_vector*1000:.1f} ms")
        
if __name__ == __main__:
    parser = argparse.ArgumentParser(description="Arguments for Myntra Scraper.")
    parser.add_argument('--run', type=str, required=True, default=1, help="'benchmark' or 'full'.")
    args = parser.parse_args()
    assert args.run in ('benchmark', 'full'), "Please use --run=benchmark or --run=full."
    
    start_time = time.perf_counter()
    
    image_embeddings = torch.load('image_embeddings_normalized.pt')
    assert image_embeddings[0].norm() == 1.0, "Image embeddings aren't normalized."
    
    index = faiss.IndexFlatIP(image_embeddings.shape[1])
    index.add(image_embeddings.detach().numpy())
    
    similar_products_cache = torch.from_numpy(compute_similar_products_cache(index, image_embeddings))
    torch.save(similar_products_cache, 'similar_products_cache.pt')
    
    print("Done...")
    print(f"The pipeline took {(time.perf_counter() - start_time) // 60} minutes.")
    
    print(f"Wrote the following files to disk:")
    print(f"similar_products_cache.pt : {os.path.getsize('similar_products_cache.pt') / 1e9:.2f} GB")