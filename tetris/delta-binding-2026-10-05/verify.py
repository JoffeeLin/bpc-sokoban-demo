"""Reproduce observations, including failures; this is not a game-success gate."""
from pathlib import Path
import hashlib,json,re,sys

LABELS=['priority','next','delta','split_next','split_delta','carrier_next','carrier_delta']
FULL=['priority','next','carrier_next','carrier_delta']
def need(ok,message):
    if not ok:raise SystemExit(message)
def read(root,name):
    p=root/name
    if not p.exists():p=root/'evidence'/name
    return p.read_text()
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def normalized(s):return re.sub(r' CPU_SECONDS=\S+','',s)
def rows(s,prefix):
    return [dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in s.splitlines() if line.startswith(prefix)]

def sources():
    home=Path(__file__).resolve().parent
    for folder in [home,home/'phase1']:
        frozen=json.loads((folder/'FREEZE.json').read_text())
        for name,value in frozen['sources'].items():
            need(sha(folder/name)==value,f'frozen source changed: {folder.name}/{name}')

def quick(root):
    sources()
    for label in LABELS:
        s=read(root,f'pair_{label}/pair.txt')
        need('identical_current_and_last_3_frames=1' in s,'history alias lost')
        need(s.count('PAIR_BYTES_HASH_FROZEN=1')==2,'pair field changed')
        need('PAIR_PROBE memory=1 noops=200 mode=0 exact=2/2' in s,'history probe changed')
        need(len(re.findall(r'PAIR_SELF_ROLLOUT memory=1 .*whole_exact=1',s))==2,'history closure changed')
        need('PAIR_PROBE memory=1 noops=200 mode=2 exact=0/2' in s,'history swap changed')
    for variant in ['O3','ubsan']:
        need(read(root,f'{variant}_pair/pair.txt')==read(root,'pair_carrier_delta/pair.txt'),'CPU pair disagreement')
        need(not read(root,f'{variant}_pair/stderr.txt'),'CPU pair stderr')
        for name in ['pair_memory.bin','pair_raw.bin']:
            need(sha(root/f'{variant}_pair/{name}')==sha(root/f'pair_carrier_delta/{name}'),'CPU pair bytes disagree')
    need(read(root,'header_mismatch_stderr.txt')=='field format mismatch\n','target/query mismatch accepted')
    need('PORT_XOR_INVARIANT exact=1 bits=1551600 real_steps=3973 external_inputs=1099 episodes=100' in read(root,'invariant.txt'),'carrier invariant changed')
    print('QUICK_REPRODUCED: raw history preserved; one-bit omission is redundant')

def full(root):
    quick(root)
    expected=json.loads(Path(__file__).with_name('SUMMARY.json').read_text())
    phase1={label:rows(read(root,f'phase1_pilot_{label}.txt'),'RESULT') for label in ['next','delta','split_next','split_delta']}
    keys=['seed','cells','teacher','self_prefix','whole_episodes','trace','frozen']
    for label,values in phase1.items():
        need(values==expected['phase1']['pilot'][label],'phase1 pilot differs')
        for k in range(3):
            need([values[k][key] for key in keys]==[phase1['next'][k][key] for key in keys],'phase1 predictions not equivalent')
    for label in ['next','carrier_next','carrier_delta']:
        need(rows(read(root,f'pilot_{label}.txt'),'RESULT')==expected['models'][label]['pilot'],'phase2 pilot differs')
    for label in FULL:
        e=expected['models'][label]
        for suffix in ['self','teacher','play','controls']:
            need('FIELD_BYTES_HASH_FROZEN=1' in read(root,f'full_{label}_{suffix}.txt'),f'{label} {suffix} field changed')
        for suffix in ['self','teacher']:
            s=read(root,f'full_{label}_{suffix}.txt')
            m=re.search(r'TOTAL_(?:SELF|TEACHER) exact=(\d+)/(\d+) failed_episodes=(\d+)',s)
            need(m is not None and list(map(int,m.groups()))==e[suffix]['totals'],f'{label} {suffix} metrics differ')
            actual=sum(int(row['real_steps']) for row in rows(s,suffix.upper()+' '))
            need(actual==e[suffix]['real_steps'],f'{label} actual trajectories differ')
        plays=re.findall(r'PLAY_SELF .*?exact=(\d+)/(\d+) failed_episodes=(\d+)/(\d+)',read(root,f'full_{label}_play.txt'))
        need(len(plays)==5 and [sum(int(row[j]) for row in plays) for j in range(4)]==e['play']['totals'],'continuous play differs')
        need(sha(root/f'full_{label}.bin')==e['field_sha256'],'native field bytes differ')
        need('DIAGNOSTIC_FIELD_BYTES_RESTORED=1' in read(root,f'diagnose_{label}.txt'),'diagnostic changed field')
        need(rows(read(root,f'diagnose_{label}.txt'),'RAW_DIAGNOSTIC')==e['diagnostic'],'raw error diagnostics differ')
    need(sha(root/'full_candidate_O3.bin')==sha(root/'full_carrier_delta.bin'),'full O2/O3 bytes differ')
    for suffix in ['smoke_eval','smoke_play']:
        ref=normalized(read(root,f'carrier_delta_{suffix}.txt'))
        for variant in ['candidate_O3','candidate_ubsan']:
            need(normalized(read(root,f'{variant}_{suffix}.txt'))==ref,'CPU full smoke differs')
    for variant in ['carrier_delta','candidate_O3','candidate_ubsan']:
        need(not read(root,f'{variant}_smoke_stderr.txt'),'full smoke stderr')
    b=expected['benchmark']
    need(f"TOTAL {b['exact']}/{b['n']}" in read(root,'baseline_new_self.txt'),'373-coupling benchmark changed')
    print('FULL_REPRODUCED: archived prefix/closure evidence and unchanged game benchmark')

if __name__=='__main__':
    need(len(sys.argv)==3 and sys.argv[1] in ['quick','full'],'verify.py quick|full OUTPUT')
    (quick if sys.argv[1]=='quick' else full)(Path(sys.argv[2]))
