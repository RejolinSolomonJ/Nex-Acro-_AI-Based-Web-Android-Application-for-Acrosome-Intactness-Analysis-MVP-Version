import os
import sys
import glob
from app.ml.predict import predict_single

def analyze_batch(folder_path):
    print("============================================================")
    print(f"BATCH ACROSOME ANALYSIS")
    print(f"Folder: {folder_path}")
    print("============================================================")

    if not os.path.exists(folder_path):
        print(f"[ERROR] Directory not found: {folder_path}")
        return

    # Find all images
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.heic')
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(folder_path, ext)))
        image_paths.extend(glob.glob(os.path.join(folder_path, ext.upper())))

    if not image_paths:
        print(f"[WARNING] No images found in {folder_path}.")
        return

    total_images = len(image_paths)
    print(f"Found {total_images} images. Analyzing now...\n")

    intact_count = 0
    damaged_count = 0

    for idx, img_path in enumerate(image_paths, 1):
        filename = os.path.basename(img_path)
        
        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            
            result = predict_single(image_bytes)
            classification = result["classification"]
            confidence = result["confidence"] * 100

            if classification == "intact":
                intact_count += 1
                status = f"\033[92mINTACT\033[0m" # Green
            else:
                damaged_count += 1
                status = f"\033[91mDAMAGED\033[0m" # Red
                
            print(f"[{idx}/{total_images}] {filename:<20} -> {status} (Confidence: {confidence:.1f}%)")
            
        except Exception as e:
            print(f"[{idx}/{total_images}] {filename:<20} -> [ERROR] {str(e)}")

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total Images Analyzed: {total_images}")
    print(f"Intact Count         : {intact_count}")
    print(f"Damaged Count        : {damaged_count}")
    
    intact_percentage = (intact_count / total_images) * 100
    print(f"\n>> OVERALL INTACT PERCENTAGE: {intact_percentage:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "test_images"
    analyze_batch(folder)
