import json,glob,os,re
CHAINS=['llm_set_theory','llm_formal_logic','llm_classical_language','non_llm_cipher','code_attack',
        'ir_figstep','ir_fc_flowchart','ir_low_contrast','ir_occluded','ir_mm_typo','ir_distraction_grid']
GUARDS=['wildguard','llama_guard_3_8b','qwen3guard_gen_8b','thinkguard','guardreasoner_vl_7b']
# POST-FIX per-attack means (updated 2026-08-07). The previous constants were the PRE-audit
# values (20.1/11.2, 18.3/16.5, 19.7/9.8, 20.8/15.4, 17.6/11.1) recorded before `b266892`
# rebuilt code_attack + ir_figstep; checking against them now fails on every correct number.
# Floor moves 28.0 -> 26.7 for the same reason.
RECORDED={('wildguard','gb'):19.4,('wildguard','mc'):10.8,('llama_guard_3_8b','gb'):17.0,('llama_guard_3_8b','mc'):16.7,
          ('qwen3guard_gen_8b','gb'):19.1,('qwen3guard_gen_8b','mc'):10.0,('thinkguard','gb'):20.4,('thinkguard','mc'):15.3,
          ('guardreasoner_vl_7b','gb'):17.8,('guardreasoner_vl_7b','mc'):11.3}
RECORDED_FLOOR=26.7
def ts(n):
    m=re.search(r'_(\d{8})_(\d{6})_',n); return (m.group(1)+m.group(2)) if m else '0'
def lj(p):
    try: return json.load(open(p))
    except: return None
def ids(d):
    out={}
    for l in open(os.path.join(d,'raw_results.jsonl')):
        if l.strip():
            row=json.loads(l); out[row['id']]=bool(row.get('asr'))
    return out
def ensemble(cond,guard):
    union={}; per=[]; miss=[]
    for c in CHAINS:
        k=(cond,guard,c)
        if k not in cells: miss.append(c); continue
        m=ids(cells[k][1]); per.append(100.0*sum(m.values())/len(m))
        for i,f in m.items(): union[i]=union.get(i,False) or f
    ens=100.0*sum(union.values())/len(union) if union else float('nan')
    mean=sum(per)/len(per) if per else float('nan')
    return ens,mean,len(per),len(union),miss
def main() -> None:
    global cells
    # gather candidate rejudge dirs -> canonical cell
    # POST-FIX selection (rewritten 2026-08-07) — see `paper_c_select` for why the old
    # inline `paper_c_guard_panel` pin silently produced nine-attack ensembles.
    from src.analysis import paper_c_select as S
    shared=S.scan(); cells={}  # (cond, guard, chain) -> (ts, dir)
    for chain,d in S.scan_floor('qwen2_5_vl_7b').items(): cells[('floor','none',chain)]=('',d)
    for guard in GUARDS:
        for cond in ('gb','mc'):
            found,_=S.postfix_dirs(shared,'qwen2_5_vl_7b',guard,cond)
            for chain,d in found.items(): cells[(cond,guard,chain)]=('',d)
    # checksum + ensemble
    print("=== CHECKSUM: per-attack MEAN (mine vs recorded) ===")
    ok=True
    ens_floor,mean_floor,np_,nid_,miss_=ensemble('floor','none')
    print(f"  floor         mean={mean_floor:5.1f}  recorded={RECORDED_FLOOR}   attacks={np_} ids={nid_} miss={miss_}")
    for g in GUARDS:
        for cond,lbl in [('gb','gb'),('mc','mc')]:
            ens,mean,np_,nid_,miss_=ensemble(cond,g)
            rec=RECORDED.get((g,cond))
            flag='' if (rec and abs(mean-rec)<=0.6) else '  <-- MISMATCH'
            if flag: ok=False
            print(f"  {g:20} {cond}  mean={mean:5.1f}  recorded={rec}  ({np_} attacks, ids={nid_}){flag}")
    print("\nCHECKSUM", "PASS ✅" if ok else "FAIL ❌")
    print("\n=== ENSEMBLE (best-of-N over 11 attacks) ASR — gpt-5-mini VALIDATED ===")
    print(f"  no_defense (floor):  {ens_floor:5.1f}%   (guard-independent)")
    print(f"  {'guard':20} {'gb (guard alone)':>18} {'mc (guard+amplifier)':>22}  {'amplifier Δ':>12}")
    for g in GUARDS:
        egb,_,_,_,_=ensemble('gb',g); emc,_,_,_,_=ensemble('mc',g)
        print(f"  {g:20} {egb:17.1f}% {emc:21.1f}%  {emc-egb:11.1f}")


if __name__ == "__main__":
    main()
