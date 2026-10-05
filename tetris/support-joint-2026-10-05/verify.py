"""Verify reproducibility of the reported rejection, not game success.

quick checks the frozen history mechanism and CPU agreement; full checks
semantic metrics and native field hashes against the archived observations.
"""
from pathlib import Path
import hashlib,json,re,sys

def need(ok,message):
    if not ok:raise SystemExit(message)
def read(root,name):return (root/name).read_text()
def normalized(s):return re.sub(r" CPU_SECONDS=\S+","",s)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def quick(root):
    for mode in range(3):
        s=read(root,f'pair_{mode}/pair.txt')
        need('identical_current_and_last_3_frames=1' in s,'alias lost')
        need(s.count('PAIR_BYTES_HASH_FROZEN=1')==2,'pair field changed')
        need('PAIR_PROBE memory=1 noops=200 mode=0 exact=2/2' in s,'history probe failed')
        need(len(re.findall(r'PAIR_SELF_ROLLOUT memory=1 .*whole_exact=1',s))==2,'history closure failed')
        need('PAIR_PROBE memory=1 noops=200 mode=2 exact=0/2' in s,'memory swap lost causality')
    for variant in ['O3','ubsan']:
        need(read(root,f'{variant}_pair/pair.txt')==read(root,'pair_2/pair.txt'),'CPU pair disagreement')
        need(not read(root,f'{variant}_pair/stderr.txt'),'CPU pair stderr')
        for name in ['pair_memory.bin','pair_raw.bin']:
            need(sha(root/f'{variant}_pair/{name}')==sha(root/f'pair_2/{name}'),'CPU pair bytes disagreement')
    print('QUICK_REPRODUCED: history closure preserved; this does not mean game closure')

def full(root):
    quick(root);expected=json.loads(Path(__file__).with_name('SUMMARY.json').read_text())
    for mode in range(3):
        e=expected['models'][str(mode)]
        for suffix in ['old_self','new_self','teacher','play','controls']:
            s=read(root,f'full_{mode}_{suffix}.txt')
            need('FIELD_BYTES_HASH_FROZEN=1' in s,f'{mode} {suffix} field changed')
        for suffix,key in [('old_self','old'),('new_self','new')]:
            s=read(root,f'full_{mode}_{suffix}.txt')
            m=re.search(r'TOTAL_SELF exact=(\d+)/(\d+) failed_episodes=(\d+)',s)
            need(m is not None,'missing self metrics')
            need([int(v) for v in m.groups()]==e[key]['totals'],f'{mode} {suffix} differs')
        s=read(root,f'full_{mode}_teacher.txt');m=re.search(r'TOTAL_TEACHER exact=(\d+)/(\d+) failed_episodes=(\d+)',s)
        need([int(v) for v in m.groups()]==e['teacher']['totals'],'teacher metrics differ')
        plays=re.findall(r'PLAY_SELF .*?exact=(\d+)/(\d+) failed_episodes=(\d+)/(\d+)',read(root,f'full_{mode}_play.txt'))
        need(len(plays)==5,'missing play streams')
        sums=[sum(int(row[j]) for row in plays) for j in range(4)]
        need(sums==e['play']['totals'],'play metrics differ')
        need(sha(root/f'full_{mode}.bin')==e['field_sha256'],'field bytes differ')
        need('DIAGNOSTIC_FIELD_BYTES_RESTORED=1' in read(root,f'diagnose_{mode}.txt'),'diagnostic not restored')
        pilot=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in read(root,f'pilot_{mode}.txt').splitlines() if line.startswith('RESULT')]
        need(pilot==e['pilot'],'pilot differs')
    need(sha(root/'full_2.bin')==sha(root/'full_2_O3.bin'),'full O2/O3 bytes differ')
    for suffix in ['smoke_eval','smoke_play']:
        ref=normalized(read(root,f'2_{suffix}.txt'))
        for variant in ['2_O3','2_ubsan']:
            need(normalized(read(root,f'{variant}_{suffix}.txt'))==ref,'full CPU smoke disagreement')
    for variant in ['2','2_O3','2_ubsan']:need(not read(root,f'{variant}_smoke_stderr.txt'),'smoke stderr')
    need('TOTAL 155868/155868' in read(root,'baseline_new_self.txt'),'373-coupling baseline failed')
    print('FULL_REPRODUCED: joint support rejected; successful 373-coupling baseline preserved')

if __name__=='__main__':
    need(len(sys.argv)==3 and sys.argv[1] in ['quick','full'],'verify.py quick|full OUTPUT')
    (quick if sys.argv[1]=='quick' else full)(Path(sys.argv[2]))
