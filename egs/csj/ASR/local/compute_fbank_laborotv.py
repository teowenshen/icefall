import logging
import os
from pathlib import Path

import torch
from lhotse import CutSet, Fbank, FbankConfig, NumpyFilesWriter, cut
from lhotse.recipes.utils import read_manifests_if_cached

from icefall.utils import get_executor

# Torch's multithreaded behavior needs to be disabled or
# it wastes a lot of CPU and slow things down.
# Do this outside of main() in case it needs to take effect
# even when we are not invoking the main (e.g. when spawning subprocesses).
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

def compute_fbank_laborotv():
    src_dir = Path("data/manifests")
    output_dir = Path("data/fbank")
    num_jobs = min(15, os.cpu_count())
    num_mel_bins = 80
    
    dataset_parts = (
        "dev",
        "train"
    )
    
    manifests = read_manifests_if_cached(
        dataset_parts=dataset_parts,
        output_dir=src_dir
    )
    assert manifests is not None
    logging.info(f"Manifests read.")
    
    extractor = Fbank(FbankConfig(num_mel_bins=num_mel_bins))
    
    with get_executor() as ex: # Initialize the executor only once
        for partition, m in manifests.items():
            if (output_dir / f"cuts_{partition}.json.gz").is_file():
                logging.info(f"{partition} already exists - skipping.")
                continue
            logging.info(f"Processing {partition}")
            cut_set = CutSet.from_manifests(
                recordings=m["recordings"],
                supervisions=m["supervisions"]
            )
            
            cut_set = (
                cut_set
                + cut_set.perturb_speed(0.9)
                + cut_set.perturb_speed(1.1)
            )
                
            cut_set = cut_set.compute_and_store_features(
                extractor=extractor,
                storage_path=f"{output_dir}/feats_{partition}",
                # when an executor is specified, make more partitions
                num_jobs=num_jobs if ex is None else 80,
                executor=ex,
                storage_type=NumpyFilesWriter
            )
            cut_set.to_json(output_dir / f"cuts_{partition}.json.gz")
            
if __name__ == "__main__":
    formatter = (
        "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    )

    logging.basicConfig(format=formatter, level=logging.INFO)

    compute_fbank_laborotv()