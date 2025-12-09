"""
Combine all batch files into a single file
"""
import pandas as pd
import glob
from datetime import datetime

OUTPUT_PATH = 'C:/Users/anhpd/OneDrive/Desktop/projects/phillipine-rental-price/data'

# Find all batch files
batch_files = sorted(glob.glob(f"{OUTPUT_PATH}/property_details_batch_*.csv"))

print(f"Found {len(batch_files)} batch files")

# Combine all batches
dfs = []
for file in batch_files:
    print(f"Loading: {file}")
    df = pd.read_csv(file)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Remove duplicates
combined_df = combined_df.drop_duplicates(subset=['url']).reset_index(drop=True)

# Save combined file
output_file = f"{OUTPUT_PATH}/property_details_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n✅ Combined {len(combined_df)} properties")
print(f"💾 Saved: {output_file}")

# Summary
successful = len(combined_df[combined_df['scrape_status'] == 'success'])
failed = len(combined_df[combined_df['scrape_status'] != 'success'])
print(f"\n📊 FINAL SUMMARY:")
print(f"   Successful: {successful}")
print(f"   Failed: {failed}")