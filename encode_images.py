"""
Example Command : python encode_images.py --images_root_dir=images

NOTE
1. This binary reads the images from specified root directory, processes them (mean/std adjustment and random-cropping),
and then encodes their embeddings. 
2. It ~2.5 hours for 1.5M images of size h x 224 (h as per 4/3 aspect ratio) on MPS

Requirements: pip install torch open_clip_torch

Ouputs:
1. image_embeddings_normalized.pt
2. ordered_image_paths.json
"""

import torch
from tqdm import tqdm
import os
from PIL import Image
import open_clip
import time
import argparse
import json
import torch.nn.functional as F


torch.set_grad_enabled(False)

## Get best available device.
def get_device():
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'


## Load the model. 
def load_model(device):
    model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
    model = model.to(device)
    model = torch.compile(model)
    return model, preprocess



def encode_images(model, preprocess, image_paths):
    ## Generate Embeddings. 
    image_embeddings = torch.zeros(size=(len(image_paths), 512))
    batch_size = 256
    for batch_start in tqdm(range(0, len(image_paths), batch_size)):
        batch_end = batch_start + batch_size
        processed_images = [preprocess(Image.open(image_path)) for image_path in image_paths[batch_start:batch_end]]
        processed_tensors = torch.stack(processed_images).to(model.device)
        image_embeddings[batch_start:batch_end] = model.encode_image(processed_tensors)
    
if __name__ == '__main__':
    ## ==== Argumentr parsing ===== ## 
    parser = argparse.ArgumentParser(description="Arguments for encode_images.py.")
    parser.add_argument('--images_root_dir', type=int, required=True, default=1, help="root dir for images. images/ ? ")
    
    args = parser.parse_args()
    ## ============================ ## 
    
    
    start_time = time.perf_counter()
    device = get_device()
    print('DEVICE : ', device)
    
    print('Loading model...')
    model, preprocess = load_model(device)
    
    print('Loading image paths...')
    image_filenames = os.listdir(args.images_root_dir)
    image_paths = [os.path.join(args.images_root_dir, filename) for filename in image_filenames]
    
    print('Encoding images...')
    image_embeddings = encode_images(model, preprocess, image_paths)
    
    print('Saving image_paths order, and image embeddings..')
    ## save embeddings and image_paths. 
    image_embeddings= F.normalize(image_embeddings, dim=-1)
    torch.save(image_embeddings, 'image_embeddings_normalized.pt')
    
    ## save ordered image paths.
    open('ordered_image_paths.json','w').write(json.dumps(image_paths))
    
    print('Done...')
    print('The pipeline took ', (time.perf_counter() - start_time) // 60, ' minutes.')