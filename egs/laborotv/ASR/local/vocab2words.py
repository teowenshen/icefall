"""
Since the only dependency of prepare_lang_bpe.py is on the words.txt of prepare_lang.py, 
this program takes the .vocab file of the bpe model and produces words.txt in data/lang.

"""

words = ["!SIL SIL", "<SPOKEN_NOISE> SPN", "<UNK> SPN"]

with open('data/lm/jp_full_romaji_200.vocab', 'r', encoding='utf8') as fin:    
    for line in fin:
        if '<blk>' in line or '<unk>' in line or '<sos/eos>' in line:
            continue
        word, *_ = line.strip().split()
        words.append(f'{word} {word}')

words = list(set(words))        
words.sort()

with open('data/lang/lexicon.txt', 'w', encoding='utf8') as fout:
    fout.write('\n'.join(words))

    