import argparse
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from tqdm.auto import tqdm

from lhotse import validate_recordings_and_supervisions
from lhotse.audio import Recording, RecordingSet
from lhotse.recipes.utils import manifests_exist, read_manifests_if_cached
from lhotse.supervision import SupervisionSegment, SupervisionSet
from lhotse.utils import Pathlike

FULL_DATA_PARTS = (
    "eval1",
    "eval2",
    "eval3",
    "core",
    "noncore",
)

def parse_transcript_header(line : str):
    sgid, start, end, line = line.split(' ', maxsplit=3)
    return (sgid, float(start), float(end), line)

def parse_one_recording(
    morph_path : Path, 
    pron_path : Path, 
    clean_path : Path, 
    wavlist_path : Path, 
    recording_id : str
) -> Tuple[Recording, List[SupervisionSegment]]:
    with morph_path.open('r') as morph_fin, pron_path.open('r') as pron_fin, \
        clean_path.open('r') as clean_fin, wavlist_path.open('r') as wavlist_fin:
        
        morph = morph_fin.read().split('\n')
        pron = pron_fin.read().split('\n')
        clean = clean_fin.read().split('\n')
        wav = wavlist_fin.read()
        
    recording = Recording.from_file(wav, recording_id=recording_id)
    
    assert len(morph) == len(pron) == len(clean)
    supervision_segments = []
    
    for morph_line, pron_line, clean_line in zip(morph, pron, clean):
        sgid, start, end, clean_line = parse_transcript_header(clean_line)
        *_, morph_line = parse_transcript_header(morph_line)
        *_, pron_line = parse_transcript_header(pron_line)
        supervision_segments.append(
            SupervisionSegment(
                id=sgid,
                recording_id=recording_id,
                start=start,
                duration=(end-start),
                channel=0,
                language="Japanese",
                speaker=recording_id,
                text=clean_line.strip(),
                custom={
                    'morph': morph_line,
                    'pron': pron_line
                }
            )
        )
    
    return recording, supervision_segments

def prepare_csj(
    output_dir : Pathlike,
    trans_dir : Pathlike, 
    dataset_parts : Union[str, Sequence[str]] = FULL_DATA_PARTS, 
    num_jobs : int = 1
) -> Dict[str, Dict[str, Union[RecordingSet, SupervisionSet]]]:
    """
    Returns the manifests which consist of the Recordings and Supervisions.
    When all the manifests are available in the ``output_dir``, it will simply read and return them.

    :param corpus_dir: Pathlike, the path of the data dir.
    :param dataset_parts: string or sequence of strings representing dataset part names, e.g. 'train-clean-100', 'train-clean-5', 'dev-clean'.
        By default we will infer which parts are available in ``corpus_dir``.
    :param output_dir: Pathlike, the path where to write the manifests.
    :return: a Dict whose key is the dataset part, and the value is Dicts with the keys 'recordings' and 'supervisions'.
    """
    
    # corpus_dir = Path(corpus_dir)
    # assert corpus_dir.is_dir(), f"No such directory for corpus_dir: {corpus_dir}"
    trans_dir = Path(trans_dir)
    assert trans_dir.is_dir(), f"No such directory for trans_dir: {trans_dir}"

    if isinstance(dataset_parts, str):
        dataset_parts = [dataset_parts]
        
    # manifests = {}
    
    if output_dir is None:
        return 
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Maybe the manigests already exist: we can read them and save a bit of preparation time.
    # manifests = read_manifests_if_cached(
    #     dataset_parts=dataset_parts, output_dir=output_dir
    # )
    
    with ThreadPoolExecutor(num_jobs) as ex:
        for part in tqdm(dataset_parts, desc="Dataset parts"):
            logging.info(f"Processing CSJ subset: {part}")
            # if manifests_exist(part=part, output_dir=output_dir):
            #     logging.info(f"CSJ subset: {part} already prepared - skipping.")
            
            recordings = []
            supervisions = []
            part_path = trans_dir / part
            futures = []
            
            for clean in part_path.glob("*/*-clean.txt"):
                template = clean.as_posix().rstrip('-clean.txt')
                morph = Path(template + '-morph.txt')
                pron = Path(template + '-pron.txt')
                wavlist = Path(template + '-wav.list')
                spk = clean.name.rstrip('-clean.txt')
                futures.append(
                    ex.submit(parse_one_recording, morph, pron, clean, wavlist, spk)
                )
                # parse_one_recording(morph, pron, clean, wavlist, spk)

            for future in tqdm(futures, desc="Processing", leave=False):
                result = future.result()
                assert result
                recording, segments = result
                recordings.append(recording)
                supervisions.extend(segments)
            
            recording_set = RecordingSet.from_recordings(recordings)
            supervision_set = SupervisionSet.from_segments(supervisions)
            validate_recordings_and_supervisions(recording_set, supervision_set)
            
            supervision_set.to_file(output_dir / f"supervisions_{part}.json")
            recording_set.to_file(output_dir / f"recordings_{part}.json")
            
            # manifests[part] = {
            #     "recordings": recording_set,
            #     "supervisions": supervision_set
            # }
    # return manifests
    

def get_args():
    #TODO: fill in parser
    parser = argparse.ArgumentParser(description="""
             TODO"""
    )
    
    parser.add_argument("--trans-dir", type=str,
                        help="Path to output transcripts")
    parser.add_argument("--manifest-dir", type=str,
                        help="Path to save manifests")    
    parser.add_argument("--debug", action="store_true",
                        help="Use hardcoded parameters")
    
    return parser.parse_args()
    
def main():
    args = get_args()
    
    if args.debug:
        args.trans_dir = "/mnt/host/corpus/csj/retranscript"
        args.manifest_dir = "data/manifests"
    
    prepare_csj(
        # dataset_parts=['eval/eval1'],
        output_dir=args.manifest_dir,
        trans_dir=args.trans_dir,
        num_jobs=4
    )
    
if __name__ == '__main__':
    main()