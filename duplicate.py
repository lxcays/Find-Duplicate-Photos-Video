import os
import shutil
import argparse
from PIL import Image
import numpy as np
from tqdm import tqdm
import hashlib
from scipy.spatial.distance import hamming
from concurrent.futures import ThreadPoolExecutor

COMPARE_SIZE = 300
DUPLICATE_FOLDER_NAME = "_duplicates"

try:
    resampling = Image.Resampling.LANCZOS  # For Pillow >= 9.1.0
except AttributeError:
    resampling = Image.LANCZOS  # For older Pillow versions

def image_hash(img_path):
    """Generate perceptual hash for an image."""
    img = Image.open(img_path).convert("L").resize((COMPARE_SIZE, COMPARE_SIZE), resampling)
    pixels = np.array(img).flatten()
    avg = pixels.mean()
    return "".join("1" if p > avg else "0" for p in pixels)

def get_similarity_score(hash1, hash2):
    """Calculate similarity score between two hashes."""
    dist = hamming(list(hash1), list(hash2))
    return round((1 - dist) * 100, 2)  # Similarity as a percentage

def sha256_hash(file_path):
    """Generate SHA256 hash for a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def process_images(input_folder):
    """Find and move duplicate images, keeping the one in the deepest subfolder."""
    encountered_hashes = {}
    duplicates_folder = os.path.join(input_folder, DUPLICATE_FOLDER_NAME)
    os.makedirs(duplicates_folder, exist_ok=True)

    print("\nProcessing Images...")
    for root, _, files in os.walk(input_folder):
        for file in tqdm(files, desc="Scanning images"):
            if not file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                continue
            
            file_path = os.path.join(root, file)
            try:
                img_hash = image_hash(file_path)
                if img_hash in encountered_hashes:
                    existing_file = encountered_hashes[img_hash]

                    # Compare folder depth and keep the one in the subfolder
                    if file_path.count(os.sep) > existing_file.count(os.sep):
                        # Move the file in the parent folder to _duplicates
                        print(f"Moving duplicate (parent folder): {existing_file}")
                        shutil.move(existing_file, os.path.join(duplicates_folder, os.path.basename(existing_file)))
                        encountered_hashes[img_hash] = file_path  # Update to the deeper file
                    else:
                        print(f"Moving duplicate (subfolder): {file_path}")
                        shutil.move(file_path, os.path.join(duplicates_folder, os.path.basename(file_path)))
                else:
                    encountered_hashes[img_hash] = file_path
            except Exception as e:
                print(f"Error processing image {file_path}: {e}")

def process_videos(input_folder):
    """Find and move duplicate videos, keeping the one in the deepest subfolder."""
    encountered_hashes = {}
    duplicates_folder = os.path.join(input_folder, DUPLICATE_FOLDER_NAME)
    os.makedirs(duplicates_folder, exist_ok=True)

    print("\nProcessing Videos...")
    for root, _, files in os.walk(input_folder):
        for file in tqdm(files, desc="Scanning videos"):
            if not file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
                continue
            
            file_path = os.path.join(root, file)
            try:
                file_hash = sha256_hash(file_path)
                file_size = os.path.getsize(file_path)
                
                if file_hash in encountered_hashes:
                    existing_file, existing_size = encountered_hashes[file_hash]

                    # Compare folder depth and keep the one in the subfolder
                    if file_path.count(os.sep) > existing_file.count(os.sep):
                        print(f"Moving duplicate (parent folder): {existing_file}")
                        shutil.move(existing_file, os.path.join(duplicates_folder, os.path.basename(existing_file)))
                        encountered_hashes[file_hash] = (file_path, file_size)
                    else:
                        print(f"Moving duplicate (subfolder): {file_path}")
                        shutil.move(file_path, os.path.join(duplicates_folder, os.path.basename(file_path)))
                else:
                    encountered_hashes[file_hash] = (file_path, file_size)
            except Exception as e:
                print(f"Error processing video {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Duplicate Image and Video Finder')
    parser.add_argument('--inspection_folder', type=str, required=True, help='Directory to inspect for duplicates')
    args = parser.parse_args()
    
    input_folder = args.inspection_folder
    print(f"Inspection folder: {input_folder}")
    
    process_images(input_folder)
    process_videos(input_folder)
    print("\nProcessing complete. Duplicates have been moved to the '_duplicates' folder.")

if __name__ == "__main__":
    main()