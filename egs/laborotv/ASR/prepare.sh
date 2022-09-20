#!/usr/bin/env bash

set -eou pipefail

nj=4
stage=-1
stop_stage=100

# We assume dl_dir (download dir) contains the following
# directories and files. If not, they will be downloaded
# by this script automatically.
#
#  - $dl_dir/LaboroTVSpeech
#
#       - dev/ 
#           - wav/ [this is the directory of the raw wav files]
#           - text.csv [this is the transcript]
#       - train/
#           - wav/ [this is the directory of the raw wav files]
#           - text.csv [this is the transcript]
#       - lexicon.txt [this is used to construct the Lexicon fst]
#       - README.md
#       - version
#
#  - $dl_dir/musan
#      This directory contains the following directories downloaded from
#       http://www.openslr.org/17/
#
#     - music
#     - noise
#     - speech

dl_dir=$PWD/download

mkdir -p data

log() {
    local fname=${BASH_SOURCE[1]##*/}
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $*"
}

log "dl_dir: $dl_dir"

if [ $stage -le 1 ] && [ $stop_stage -ge 1 ]; then
  log "Stage 1: Prepare LaboroTV manifest"
  # We assume that you have downloaded the LaboroTV/data corpus
  # to $dl_dir/LaboroTV
  mkdir -p data/manifests
  python3 ./laborotv.py # TODO: -j $nj $dl_dir/LaboroTV data/manifests
fi

lang_dir=data/lang

if [ $stage -le 5 ] && [ $stop_stage -ge 5 ];then 
  log "Stage 5: Prepare lang dir"
  mkdir -p $lang_dir
  (echo '!SIL SIL'; echo '<SPOKEN_NOISE> SPN'; echo '<UNK> SPN'; ) |
      cat - /mnt/host/mnt/minami_data_server/dialogue_data/LaboroTVSpeech_v1.0d/data/lexicon.txt | 
      sort | uniq > $lang_dir/lexicon.txt
