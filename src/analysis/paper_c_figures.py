"""Paper C result figures — ensemble bars + safety-utility tradeoff frontier.
Numbers are the gpt-5-mini VALIDATED Qwen2.5-VL results (experiment_results.md §5-Guard Panel + §RQ4).
Regenerate with `python src/analysis/paper_c_figures.py`; add the InternVL3 2nd-model data to the DATA
block when gen2_internvl3 lands. Uses the scientific-visualization skill's publication style."""
import sys, os
SKILL = "/Users/haoyu/.claude/skills/scientific-visualization"
sys.path.insert(0, SKILL + "/scripts"); sys.path.insert(0, SKILL + "/assets")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
try:
    from style_presets import apply_publication_style; apply_publication_style('default')
except Exception as e:
    print("style preset fallback:", e)
    plt.rcParams.update({'font.size':8,'axes.labelsize':9,'font.family':'sans-serif'})
OI = ['#E69F00','#56B4E9','#009E73','#F0E442','#0072B2','#D55E00','#CC79A7','#000000']
FIGS = "paper/autoattack_defense/latex/figs"; os.makedirs(FIGS, exist_ok=True)

def wilson_err(vals, n=100, z=1.96):
    """Asymmetric Wilson 95% CI half-widths (lower,upper) for yerr; matches tab:app-stats."""
    lo, hi = [], []
    for v in vals:
        p = v/100.0; d = 1 + z*z/n
        c = (p + z*z/(2*n))/d
        h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
        lo.append(v - (c-h)*100); hi.append((c+h)*100 - v)
    return np.array([lo, hi])

# ---- DATA (Qwen2.5-VL, gpt-5-mini, n=100) — all FIVE guards ----
GUARDS = ['WildGuard','Qwen3Guard','GuardReasoner','LlamaGuard-3','ThinkGuard']
FLOOR = 89                          # no_defense ensemble (guard-independent)
GB   = [75,76,84,71,78]             # guard alone
MC   = [72,65,71,79,77]             # + recover+decode amplifier
MCRG = [43,43,58,48,54]             # + reguard layer
MC_OR   = [64,59,59.5,28,45]        # benign over-refusal %, avg(text,image), mc
MCRG_OR = [84,80.5,86.5,32.5,65.5]  #                                        mc+reguard

# ---- DATA (InternVL3-8B, gpt-5-mini, n=100) — first 3 guards, generalization ----
FLOOR2 = 91
GB2   = [81,81,90]
MC2   = [63,69,67]
MCRG2 = [48,56,65]
MC_OR2   = [84,80,82]
MCRG_OR2 = [90,86,92]

# ---- Fig 1: ensemble ASR grouped bars (5 guards + Wilson 95% CI error bars) ----
fig, ax = plt.subplots(figsize=(3.6,2.7))
x = np.arange(len(GUARDS)); w = 0.26
ekw = dict(capsize=1.6, ecolor='0.35', error_kw={'lw':0.6})
ax.axhline(FLOOR, ls='--', color=OI[7], lw=1)
ax.text(len(GUARDS)-0.5, FLOOR+1, 'no defense (89)', ha='right', va='bottom', fontsize=6, color=OI[7])
ax.bar(x-w, GB,   w, label='guard alone',           color=OI[1], yerr=wilson_err(GB),   **ekw)
ax.bar(x,   MC,   w, label='+ amplifier',           color=OI[0], yerr=wilson_err(MC),   **ekw)
ax.bar(x+w, MCRG, w, label='+ amplifier + reguard', color=OI[2], yerr=wilson_err(MCRG), **ekw)
ax.set_xticks(x); ax.set_xticklabels(GUARDS, rotation=22, ha='right', fontsize=6)
ax.set_ylabel('Ensemble attack-success rate (%)'); ax.set_ylim(0,100)
ax.legend(frameon=False, fontsize=6, loc='lower center', bbox_to_anchor=(0.5,1.0),
          ncol=3, columnspacing=1.1, handlelength=1.1, handletextpad=0.4)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout(); fig.savefig(FIGS+"/ensemble_bars.pdf"); fig.savefig(FIGS+"/ensemble_bars.png", dpi=300)

# ---- Fig 2: safety-utility tradeoff frontier (BOTH models) ----
from matplotlib.lines import Line2D
fig, ax = plt.subplots(figsize=(3.5,2.9))
def plot_model(MCv, MCRGv, ORv, ORrgv, m_mc, m_rg, ls):
    for i in range(len(MCv)):
        ax.annotate('', xy=(ORrgv[i],MCRGv[i]), xytext=(ORv[i],MCv[i]),
                    arrowprops=dict(arrowstyle='->', color=OI[i], lw=1.2, alpha=0.85, linestyle=ls))
        ax.scatter(ORv[i],   MCv[i],   facecolors='none', edgecolors=OI[i], marker=m_mc, s=34, zorder=3, lw=1.3)
        ax.scatter(ORrgv[i], MCRGv[i], color=OI[i],       marker=m_rg, s=34, zorder=3)
plot_model(MC,  MCRG,  MC_OR,  MCRG_OR,  'o', 's', '-')    # Qwen2.5-VL (5 guards)
plot_model(MC2, MCRG2, MC_OR2, MCRG_OR2, '^', 'D', '--')   # InternVL3 (first 3 guards)
ax.set_xlabel('Benign over-refusal (%)  →  worse utility')
ax.set_ylabel('Ensemble ASR (%)  →  worse safety')
guard_handles=[Line2D([0],[0],color=OI[i],lw=2.4,label=g) for i,g in enumerate(GUARDS)]
model_handles=[Line2D([0],[0],color='0.35',marker='o',mfc='none',ls='-', label='Qwen2.5-VL'),
               Line2D([0],[0],color='0.35',marker='^',mfc='none',ls='--',label='InternVL3')]
leg1=ax.legend(handles=guard_handles, frameon=False, fontsize=6, loc='upper left', title='guard', title_fontsize=6)
ax.add_artist(leg1)
ax.legend(handles=model_handles, frameon=False, fontsize=6, loc='lower right')
ax.text(0.02,0.02,'open = amplifier → filled = +reguard', transform=ax.transAxes, fontsize=5.5, ha='left')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout(); fig.savefig(FIGS+"/tradeoff_frontier.pdf"); fig.savefig(FIGS+"/tradeoff_frontier.png", dpi=300)
print("wrote:", os.listdir(FIGS))
