import argparse
import logging
import os
from pathlib import Path

import torch
from lhotse import CutSet, Fbank, FbankConfig, ChunkedLilcomHdf5Writer
from lhotse.recipes.utils import read_manifests_if_cached

from icefall.utils import get_executor

# Torch's multithreaded behavior needs to be disabled or
# it wastes a lot of CPU and slow things down.
# Do this outside of main() in case it needs to take effect
# even when we are not invoking the main (e.g. when spawning subprocesses).
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

FULL_DATA_PARTS = (
    "core",
    "eval1",
    "eval2",
    "eval3",
    "noncore",
)

def compute_fbank_csj(manifest_dir : Path, fbank_dir : Path, num_jobs = 4, num_mel_bins=80):
    # a = FbankConfig(num_mel_bins=num_mel_bins)
    extractor = Fbank(FbankConfig(num_mel_bins=num_mel_bins))
    num_jobs = min(num_jobs, os.cpu_count())
    
    manifests = read_manifests_if_cached(
        dataset_parts=FULL_DATA_PARTS,
        output_dir=manifest_dir,
        suffix='json'
    )
    assert manifests 
    logging.info(f"Manifests read.")    
    
    with get_executor() as ex: # Initialise the executor only once 
        for partition, m in manifests.items():
            if (manifest_dir / f"cuts_{partition}.jsonl.gz").is_file():
                logging.info(f"{partition} already exists - skipping.")
                continue
            
            logging.info(f"Processing {partition}")
            cut_set = CutSet.from_manifests(
                recordings=m["recordings"],
                supervisions=m["supervisions"]
            )

            cut_set = cut_set.trim_to_supervisions(keep_overlapping=False)
            
            cut_set = (
                cut_set 
                + cut_set.perturb_speed(0.9)
                + cut_set.perturb_speed(1.1)
            )
            
            cut_set = cut_set.compute_and_store_features(
                extractor=extractor,
                storage_path=(fbank_dir / f"feats_{partition}").as_posix(),
                num_jobs=num_jobs if ex is None else 80,
                executor=ex,
                storage_type=ChunkedLilcomHdf5Writer
            )

            cut_set.to_jsonl(manifest_dir / f"cuts_{partition}.jsonl.gz")

def get_args():
    #TODO: fill in parser
    parser = argparse.ArgumentParser(description="""
             TODO"""
    )
    
    parser.add_argument("--manifest-dir", type=str,
                        help="Path to save manifests")    
    parser.add_argument("--fbank-dir", type=str,
                        help="Path to save fbank features")    
    parser.add_argument("--debug", action="store_true",
                        help="Use hardcoded parameters")
    
    return parser.parse_args()
    
def main():
    args = get_args()
    
    if args.debug:
        args.manifest_dir = "data/manifests"
        args.fbank_dir = "/mnt/minami_data_server/t2131178/corpus/JP_Speech/fbank"
    
    args.manifest_dir = Path(args.manifest_dir)
    args.fbank_dir = Path(args.fbank_dir)

    formatter = (
        "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    )

    logging.basicConfig(format=formatter, level=logging.INFO)

    if not (args.fbank_dir / ".done").exists():
        compute_fbank_csj(
            manifest_dir=args.manifest_dir,
            fbank_dir=args.fbank_dir,
            num_jobs=15,
            num_mel_bins = 80
        )
        logging.info("All fbank computed for CSJ.")
        (args.fbank_dir / ".done").touch()
    else:
        logging.info("Previous fbank computed for CSJ found.")
    
if __name__ == '__main__':
    main()  