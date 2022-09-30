import argparse
from ast import literal_eval
import json
from pathlib import Path
from typing import Dict, Iterable, List


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--lang-dir",
        type=Path,
        help="Path to lang directory"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use hardcoded arguments. "
    )

    return parser

def deserialise_tuple_dict(d) -> Dict:
    """Returns a dict with all string keys deserialised into tuples. 
    Assumes that all keys are the same type.

    Args:
        d (Dict): The dictionary to be deserialised. Typically the 
            result of a json.loads

    Returns:
        Dict: Deserialised dict. 
    """    
    if not d:
        return d
    elif isinstance(d, Dict) and '(' in next(iter(d)):
        return {
            literal_eval(k) : deserialise_tuple_dict(v)
                for k, v in d.items()
        }
    elif isinstance(d, Dict):
        return {
            k : deserialise_tuple_dict(v)
            for k, v in d.items()
        }
    elif isinstance(d, List):
        return [deserialise_tuple_dict(dd) for dd in d]
    elif isinstance(d, Iterable) and '(' in d:
        return literal_eval(d)
    else:
        return d
    

def main():
    args = get_parser().parse_args()
    if args.debug:
        #args.msp = "lang_ori/msp_dict.json"
        args.lang_dir = Path("lang_char")

    with (args.lang_dir / "msp_dict.json").open("r") as fin:
        msp_dict = deserialise_tuple_dict(json.loads(fin.read()))
    
    tokens = set()
    words = set()
    for morph, v in msp_dict.items():
        for pron, vv in v.items():
            out_pron = vv['out_pron']
            out_surface = vv['out_surface']
            if not isinstance(out_pron, List):
                out_pron = [out_pron]
            if not isinstance(out_surface, List):
                out_surface = [out_surface]

            tokens.update(p for pron in out_pron for p in pron)
            out_surface = [w.split('+')[0] for w in out_surface]
            out_surface = [w for w in out_surface if w]
            words.update(w for word in out_surface for w in list(word))            

    words = sorted(words)
    tokens = sorted(tokens)
    
    with (args.lang_dir / "tokens.txt").open("w") as fout:
        fout.write("<blk>\t0\n")

        for i, token in enumerate(tokens, 1):
            fout.write(f"{token}\t{i}\n")

    with (args.lang_dir / "words.txt").open("w") as fout:
        fout.write("<blk>\t0\n")

        for i, word in enumerate(words, 1):
            fout.write(f"{word}\t{i}\n")

    with (args.lang_dir / "words_len").open("w") as fout:
        fout.write(f"{len(words)+1}")
    
    with (args.lang_dir / "tokens_len").open("w") as fout:
        fout.write(f"{len(tokens)+1}")

if __name__ == '__main__':
    main()