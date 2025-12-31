import subprocess
from pathlib import Path

import spatialdata_data_converter.config as sdcc

# Datasets from spatialdata-io .github/workflows/prepare_test_data.yaml
SPATIALDATA_IO_DEV_DATASETS = {
    # 10x Genomics Xenium 2.0.0 (CC BY 4.0 license)
    'Xenium_V1_human_Breast_2fov_outs': 'https://cf.10xgenomics.com/samples/xenium/2.0.0/Xenium_V1_human_Breast_2fov/Xenium_V1_human_Breast_2fov_outs.zip',
    'Xenium_V1_human_Lung_2fov_outs': 'https://cf.10xgenomics.com/samples/xenium/2.0.0/Xenium_V1_human_Lung_2fov/Xenium_V1_human_Lung_2fov_outs.zip',
    # 10x Genomics Xenium 3.0.0 (5K) Mouse ileum, nuclear expansion
    'Xenium_Prime_Mouse_Ileum_tiny_outs': 'https://cf.10xgenomics.com/samples/xenium/3.0.0/Xenium_Prime_Mouse_Ileum_tiny/Xenium_Prime_Mouse_Ileum_tiny_outs.zip',
    # 10x Genomics Xenium 4.0.0 (v1) Human ovary, nuclear expansion
    'Xenium_V1_Human_Ovary_tiny_outs': 'https://cf.10xgenomics.com/samples/xenium/4.0.0/Xenium_V1_Human_Ovary_tiny/Xenium_V1_Human_Ovary_tiny_outs.zip',
    # 10x Genomics Xenium 4.0.0 (v1) Human ovary, multimodal cell segmentation
    'Xenium_V1_MultiCellSeg_Human_Ovary_tiny_outs': 'https://cf.10xgenomics.com/samples/xenium/4.0.0/Xenium_V1_MultiCellSeg_Human_Ovary_tiny/Xenium_V1_MultiCellSeg_Human_Ovary_tiny_outs.zip',
    # 10x Genomics Xenium 4.0.0 (v1+Protein) Human kidney, multimodal cell segmentation
    'Xenium_V1_Protein_Human_Kidney_tiny_outs': 'https://cf.10xgenomics.com/samples/xenium/4.0.0/Xenium_V1_Protein_Human_Kidney_tiny/Xenium_V1_Protein_Human_Kidney_tiny_outs.zip',
    # 10x Genomics Visium HD 4.0.1 (CC BY 4.0 license)
    'Visium_HD_Tiny_3prime_Dataset_outs': 'https://cf.10xgenomics.com/samples/spatial-exp/4.0.1/Visium_HD_Tiny_3prime_Dataset/Visium_HD_Tiny_3prime_Dataset_outs.zip',
    # Spatial Genomics seqFISH v2 (permission granted for public use)
    'seqfish-2-test-dataset': 'https://s3.embl.de/spatialdata/raw_data/seqfish-2-test-dataset.zip',
}


def download_spatialdata_io_dev_datasets_func():
    """Download spatialdata-io dev/test datasets."""
    data_dir = Path(sdcc.Config.REPOSITORIES_FOLDER) / 'spatialdata-io' / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    for name, url in SPATIALDATA_IO_DEV_DATASETS.items():
        zip_file = data_dir / f"{name}.zip"
        extract_dir = data_dir / name

        print(f"Downloading {name}...")
        subprocess.run(['curl', '-o', str(zip_file), url], check=True)

        print(f"Extracting {name}...")
        extract_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(['unzip', '-o', str(zip_file), '-d', str(extract_dir)], check=True)

        print(f"Removing {zip_file}...")
        zip_file.unlink()

    print("Done downloading spatialdata-io dev datasets.")
