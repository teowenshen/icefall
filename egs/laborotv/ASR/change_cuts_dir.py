from lhotse.serialization import save_to_json, load_json
from lhotse.cut import MonoCut, CutSet

parts = ['test'] #['dev', 'train']

#path = '/mnt/minami_data_server/t2131178/icefall-old/egs/laborotv-old/data/fbank/cuts_dev.json.gz'

#cuts = load_json(path)

for part in parts:
    from_path = f'/mnt/minami_data_server/t2131178/icefall-old/egs/laborotv-old/data/fbank/cuts_{part}.json.gz'
    cuts = load_json(from_path)
    to_path = f'/mnt/minami_data_server/t2131178/icefall/egs/laborotv/ASR/data/fbank/cuts_{part}.json.gz'
    for i in range(len(cuts)):
        ct = cuts[i]
        for j in range(len(ct['supervisions'])):
            ct['supervisions'][j]['text'] = ct['supervisions'][j]['text'].replace(' ', '')
        ct['features']['storage_path'] = ct['features']['storage_path'].replace('../data/fbank', 'data/fbank')
        ct['recording']['sources'][0]['source'] = ct['recording']['sources'][0]['source'].replace('/mnt/host', '')
        cuts[i] = ct
    save_to_json(cuts, to_path)
    