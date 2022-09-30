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
trans_dir=$csj_dir/retranscript_kaldi
fbank_dir=$csj_dir/fbank
lang_dir=lang_kaldi

. shared/parse_options.sh || exit 1

mkdir -p data

log() {
    local fname=${BASH_SOURCE[1]##*/}
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $*"
}

if [ $stage -le 0 ] && [ $stop_stage -ge 0 ]; then 
    log "Stage 0: Make CSJ Transcript and prepare lang"
    # python notify_tg.py "Stage 0: Make CSJ Transcript and prepare lang"
    python -O CSJSDB_Parser/csj_make_transcript.py --corpus-dir $csj_dir \
        --trans-dir $trans_dir --lang-dir $lang_dir
    python local/prepare_lang_kaldi.py --lang-dir $lang_dir
fi

if [ $stage -le 1 ] && [ $stop_stage -ge 1 ]; then 
    log "Stage 1: Prepare CSJ manifest"
    mkdir -p data/manifests_kaldi
    if [ ! -e data/manifests_kaldi/.csj.done ]; then
        # python notify_tg.py "Stage 1: Prepare CSJ manifest"
        python -O local/lhotse_prepare_csj.py --trans-dir $trans_dir \
            --manifest-dir data/manifests_kaldi
        touch data/manifests_kaldi/.csj.done
    fi
fi

if [ $stage -le 2 ] && [ $stop_stage -ge 2 ]; then
    log "Stage 2: Prepare musan manifest"
    mkdir -p $musan_dir/manifests
    if [ ! -e $musan_dir/manifests/.musan.done ]; then
        lhotse prepare musan $musan_dir $musan_dir/manifests
        touch $musan_dir/manifests/.musan.done
    fi
fi

if [ $stage -le 3 ] && [ $stop_stage -ge 3 ]; then 
    log "Stage 3: Compute fbank for CSJ"
    # python notify_tg.py "Stage 3: Compute fbank for CSJ"
    mkdir -p $fbank_dir
    python -O local/compute_fbank_csj.py --manifest-dir data/manifests --fbank-dir $fbank_dir
    # python notify_tg.py "Stage 3: Compute fbank for CSJ - Done"
    if [ ! -e $fbank_dir/.csj-validated.done ]; then 
        log "Validating fbank directory for CSJ"
        parts=(
            core
            noncore
            eval1
            eval2
            eval3
        )
        for part in ${parts[@]}; do
            python local/validate_manifest.py --manifest data/manifests/cuts_${part}.jsonl.gz
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

if [ $stage -le 5 ] && [ $stop_stage -ge 5 ]; then 
    log "Start training"
    python conv_emformer_transducer_stateless2/train.py --testset eval2 --world-size 1 \
        --noncore --manifest-dir data/manifests --musan-dir /mnt/minami_data_server/t2131178/corpus/musan/musan/fbank \
        --max-duration 150 --num-epochs 25 --lang-dir lang_char 
fi

if [ $stage -le 6 ] && [ $stop_stage -ge 6 ]; then 
    log "Start decoding"
    python conv_emformer_transducer_stateless2/decode.py --testset eval1 eval2 eval3 \
        --manifest-dir data/manifests --musan-dir /mnt/minami_data_server/t2131178/corpus/musan/musan/fbank \
        --max-duration 150 --decoding-method modified_beam_search \
        --beam-size 4 --epoch 9 --avg 3 --lang-dir lang_char 
fi