#!/usr/bin/env python3
"""
Download VedAstro's 15,000 Celebrity Dataset from Hugging Face
and prepare a subset for blind testing.
"""
from pathlib import Path
from datasets import load_dataset
import json
import pandas as pd

def download_and_prepare_dataset():
    """Download the VedAstro celebrity dataset and prepare samples for testing."""
    
    print("📥 Downloading VedAstro Celebrity Dataset from Hugging Face...")
    
    # Download the dataset
    # Try different possible paths
    possible_paths = [
        "VedAstro/15000-Famous-People-Birth-Date-Location",
        "vedastro/15000-Famous-People-Birth-Date-Location",
        "VedAstro/FamousPeople",
    ]
    
    dataset = None
    for path in possible_paths:
        try:
            print(f"Trying: {path}...")
            dataset = load_dataset(path)
            print(f"✅ Found dataset at: {path}")
            break
        except Exception as e:
            print(f"  ❌ {path} failed: {str(e)[:100]}")
            continue
    
    if dataset is None:
        print("\n⚠️ Could not access VedAstro dataset from Hugging Face.")
        print("Falling back to manual CSV download approach...")
        return None
    
    try:
        dataset = load_dataset("VedAstro/15000-Famous-People-Birth-Date-Location")
        print(f"✅ Dataset Downloaded! {len(dataset['train'])} records found.")
        
        # Convert to pandas for easier manipulation
        df = pd.DataFrame(dataset['train'])
        
        # Save the full dataset locally
        output_dir = Path(__file__).parent / 'vedastro_data'
        output_dir.mkdir(exist_ok=True)
        
        full_csv = output_dir / 'vedastro_15k_full.csv'
        df.to_csv(full_csv, index=False)
        print(f"💾 Full dataset saved to: {full_csv}")
        
        # Display column names
        print(f"\n📊 Dataset Columns: {list(df.columns)}")
        print(f"\n🔍 Sample Record:")
        print(df.head(1).to_dict('records')[0])
        
        # Select 10 high-quality profiles for testing
        # Prioritize records with complete data
        print("\n🎯 Selecting 10 celebrity profiles for blind testing...")
        
        # Filter out records with missing critical data
        df_filtered = df.dropna(subset=['Name'])  # At minimum, we need name
        
        # Sample 10 records
        sample_df = df_filtered.sample(n=min(10, len(df_filtered)), random_state=42)
        
        sample_csv = output_dir / 'vedastro_sample_10.csv'
        sample_df.to_csv(sample_csv, index=False)
        print(f"✅ Sample saved to: {sample_csv}")
        
        # Display the selected celebrities
        print("\n📋 Selected Celebrities:")
        for idx, row in sample_df.iterrows():
            print(f"  - {row.get('Name', 'Unknown')}")
        
        return output_dir
        
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    download_and_prepare_dataset()
