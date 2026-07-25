import json,glob,os,re
CHAINS=['llm_set_theory','llm_formal_logic','llm_classical_language','non_llm_cipher','code_attack','ir_figstep','ir_fc_flowchart','ir_low_contrast','ir_occluded','ir_mm_typo','ir_distraction_grid']
GUARDS=['wildguard','qwen3guard_gen_8b','guardreasoner_vl_7b']
def lj(p):
    try: return json.load(open(p))
    except: return None
def ts(n):
    m=re.search(r'_(\d{8})_(\d{6})_',n); return (m.group(1)+m.group(2)) if m else '0'
def ids(d):
    out={}
    for l in open(os.path.join(d,'raw_results.jsonl')):
        if l.strip(): row=json.loads(l); out[row['id']]=bool(row.get('asr'))
    return out
def ens(cond,g):
    u={}; per={}
    for c in CHAINS:
        k=(cond,g,c)
        if k not in sel: continue
        m=ids(sel[k][1]); per[c]=100.0*sum(m.values())/len(m)
        for i,f in m.items(): u[i]=u.get(i,False) or f
    return (100.0*sum(u.values())/len(u) if u else float('nan')), per, len(per)
def main() -> None:
    global sel
    sel={}
    for d in glob.glob('outputs/autoattack_defense/rejudge/harmbench/*gpt-5-mini*'):
        r=lj(d+'/results.json')
        if not r or r.get('asr') is None: continue
        enc=r.get('encoding'); src=(r.get('upstream_ref') or {}).get('source_dir','')
        chain=enc if enc in CHAINS else next((c for c in CHAINS if f'_{c}_' in src),None)
        if chain is None: continue
        s=lj(src+'/results.json') or {}
        dc=s.get('defense_config') or {}; guard=dc.get('guard_model','none'); camp=s.get('campaign')
        dtext=dc.get('decode_text'); dstyle=dc.get('decode_style')
        if camp=='paper_c_guard_panel' and r.get('defense')=='guard_baseline' and guard in GUARDS: cond=('gb',guard)
        elif camp=='paper_c_guard_panel' and r.get('defense')=='modality_complete' and guard in GUARDS and dtext==True and dstyle=='recover': cond=('mc',guard)
        elif camp=='paper_c_reguard_ablation' and guard in GUARDS: cond=('mcrg',guard)
        else: continue
        k=(cond[0],cond[1],chain); t=ts(os.path.basename(d))
        if k not in sel or t>sel[k][0]: sel[k]=(t,d)
    print(f'{"guard":20}{"gb":>6}{"mc":>6}{"mc+rg":>7}    code_attack coverage gb/mc/mcrg    n(gb/mc/mcrg)')
    print('-'*92)
    for g in GUARDS:
        egb,pgb,ngb=ens('gb',g); emc,pmc,nmc=ens('mc',g); erg,prg,nrg=ens('mcrg',g)
        code='%.0f/%.0f/%.0f'%(pgb.get('code_attack',-1),pmc.get('code_attack',-1),prg.get('code_attack',-1))
        print(f'{g:20}{egb:5.0f}%{emc:5.0f}%{erg:6.0f}%    {code:>28}    {ngb}/{nmc}/{nrg}')
    print()
    print('ENSEMBLE = fraction of 100 behaviors broken by ANY of the 11 attacks (gpt-5-mini). Lower=better.')


if __name__ == "__main__":
    main()
