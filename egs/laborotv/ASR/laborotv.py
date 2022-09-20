import logging
import re
import shutil
import tarfile
import zipfile
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from tqdm.auto import tqdm

from lhotse import validate_recordings_and_supervisions
from lhotse.audio import Recording, RecordingSet
from lhotse.recipes.utils import manifests_exist, read_manifests_if_cached
from lhotse.supervision import AlignmentItem, SupervisionSegment, SupervisionSet
from lhotse.utils import Pathlike

FULL_DATA_PARTS = (
    "dev",
    "train"
)

def prepare_laborotv(
    corpus_dir: Pathlike,
    output_dir: Pathlike,
    trans_dir : Pathlike,
    dataset_parts: Union[str, Sequence[str]] = FULL_DATA_PARTS,
    num_jobs: int = 1,
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
    
    corpus_dir = Path(corpus_dir)
    assert corpus_dir.is_dir(), f"No such directory: {corpus_dir}"
    
    if isinstance(dataset_parts, str):
        dataset_parts = [dataset_parts]
        
    manifests = {}
    
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        #Maybe the manigests already exist: we can read them and save a bit of preparation time.
        # manifests = read_manifests_if_cached(
        #     dataset_parts=dataset_parts, output_dir=output_dir
        # )
        
        with ThreadPoolExecutor(num_jobs) as ex:
            for part in tqdm(dataset_parts, desc="Dataset parts"):
                # logging.info(f"Processing LaboroTV subset: {part}")
                # if manifests_exist(part=part, output_dir=output_dir):
                #    logging.info(f"LaboroTV subset: {part} already prepared - skipping.")
                    
                recordings = []
                supervisions = []
                part_path = corpus_dir / "data" / part
                wav_path = part_path / "wav"
                trans_part = trans_dir / f"text_{part}.txt"
                futures = []
                
                with open(trans_part, 'r') as f:
                    for line in f:
                        futures.append(
                            ex.submit(parse_utterance, wav_path, line)
                        )
                        
                for future in tqdm(futures, desc="Processing", leave=False):
                    result = future.result()
                    if result is None:
                        continue
                    recording, segment = result
                    recordings.append(recording)
                    supervisions.append(segment)
                    
                recording_set = RecordingSet.from_recordings(recordings)
                supervision_set = SupervisionSet.from_segments(supervisions)
                validate_recordings_and_supervisions(recording_set, supervision_set)
                
                if output_dir is not None:
                    supervision_set.to_file(output_dir / f"supervisions_{part}.json")
                    recording_set.to_file(output_dir / f"recordings_{part}.json")
                    
                manifests[part] = {
                    "recordings": recording_set,
                    "supervisions": supervision_set
                }
                
            return manifests

def parse_utterance(
    dataset_split_path: Path, 
    line: str
) -> Optional[Tuple[Recording, SupervisionSegment]]:
    recording_id, text = line.strip().split(',', maxsplit=1)
    
    # Create the Recording first
    
    audio_path = (
        dataset_split_path 
        / f"{recording_id}.wav"
    )
    
    if not audio_path.is_file():
        logging.warning(f"No such file: {audio_path}")
        return None
    
    recording = Recording.from_file(audio_path, recording_id=recording_id)
    # Then, create the corresponding supervisions
    
    segment = SupervisionSegment(
        id=recording_id,
        recording_id=recording_id,
        start=0.0,
        duration=recording.duration,
        channel=0,
        language="Japanese",
        speaker=recording_id,
        text = text.strip()
    )

    return recording, segment
    
# TODO: Expose corpus_dir, output_dir, num_jobs
def main():
    corpus_dir = Path("/mnt/minami_data_server/dialogue_data/LaboroTVSpeech_v1.0d")
    trans_dir = Path("/mnt/minami_data_server/t2131178/Workspace/LaboroTV_Romaji_Transcript/outputs")
    output_dir = Path("data/manifests")
    
    
    prepare_laborotv(
        corpus_dir=corpus_dir, 
        dataset_parts=['dev', 'train'], #FULL_DATA_PARTS, 
        output_dir=output_dir,
        trans_dir=trans_dir,
        num_jobs=4)
    
if __name__ == '__main__':
    main()
    
