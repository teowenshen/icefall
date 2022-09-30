mkdir -p data/results
for m in fast_beam_search modified_beam_search; do
    for epoch in 25 26 27 28; do
        for avg in 10 8 6 4 2; do
            for b in 4 8 12 16; do  
                python conv_emformer_transducer_stateless2/decode.py \
                    --epoch $epoch \
                    --avg $avg \
                    --exp-dir conv_emformer_transducer_stateless2/exp \
                    --max-duration 150 \
                    --decoding-method $m \
                    --beam $b \
                    --max-contexts 4 \
                    --max-states 8 \
                    --beam-size $b \
                    --manifest-dir data/manifests --musan-dir /mnt/minami_data_server/t2131178/corpus/musan/musan/fbank \
                    --lang-dir lang_char \
                    --testset eval1 eval2 eval3 
            done
        done
    done
    cp -r conv_emformer_transducer_stateless2/exp/$m/wer-summary-*.txt data/results/
done