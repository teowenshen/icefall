#!/usr/bin/env bash

set -eou pipefail

nj=15
stage=-1
stop_stage=100

# We assume the following directories are downloaded.
#
#  - $csj_dir
#  - $musan_dir
#      This directory contains the following directories downloaded from
#       http://www.openslr.org/17/
#
#     - music
#     - noise
#     - speech

csj_dir=/mnt/minami_data_server/t2131178/corpus/JP_Speech
musan_dir=/mnt/minami_data_server/t2131178/corpus/musan/musan
trans_dir=$csj_dir/retranscript
fbank_dir=$csj_dir/fbank
lang_dir=lang_ori

. shared/parse_options.sh || exit 1

mkdir -p data

log() {
    local fname=${BASH_SOURCE[1]##*/}
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $*"
}

if [ $stage -le 0 ] && [ $stop_stage -ge 0 ]; then 
    log "Stage 0: Make CSJ Transcript"
    python -O CSJSDB_Parser/csj_make_transcript.py --corpus-dir $csj_dir \
        --trans-dir $trans_dir --lang-dir $lang_dir
fi

if [ $stage -le 1 ] && [ $stop_stage -ge 1 ]; then 
    log "Stage 1: Prepare CSJ manifest"
    mkdir -p data/manifests
    python -O local/lhotse_prepare_csj.py --trans-dir $trans_dir \
        --manifest-dir data/manifests
fi

if [ $stage -le 2 ] && [ $stop_stage -ge 1 ]; then
    log "Stage 2: Prepare musan manifest"
    mkdir -p $musan_dir/manifests
    if [ ! -e data/manifests/.musan.done ]; then
        lhotse prepare musan $musan_dir $musan_dir/manifests
        touch data/manifests/.musan.done
    fi
fi

if [ $stage -le 3 ] && [ $stop_stage -ge 3 ]; then 
    log "Stage 3: Compute fbank for CSJ"
    mkdir -p $fbank_dir
    python -O local/compute_fbank_csj.py --manifest-dir data/manifests --fbank-dir $fbank_dir

    if [ ! -e $fbank_dir/.csj-validated.done ]; then 
        log "Validating fbank directory for CSJ"
        parts=(
            core
            noncore
            eval1
            eval2
            eval3
            excluded
        )
        for part in ${parts[@]}; do
            python local/validate_manifest.py data/manifests/cuts_${part}.jsonl.gz
        done
		touch $fbank_dir/.csj-validated.done
    fi
    
fi

if [ $stage -le 4 ] && [ $stop_stage -ge 4 ]; then 
    log "Stage 4: Compute fbank for musan"
    mkdir -p $musan_dir/fbank
    

    if [ ! -e $musan_dir/fbank/.musan.done ]; then 
        python -O local/compute_fbank_musan.py --manifest-dir $musan_dir/manifests --fbank-dir $musan_dir/fbank
        touch $musan_dir/fbank/.musan.done
    fi
fi

