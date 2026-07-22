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

# ---- DATA (Qwen2.5-VL, gpt-5-mini, n=100) ----
GUARDS = ['WildGuard','Qwen3Guard','GuardReasoner']
FLOOR = 89                          # no_defense ensemble (guard-independent)
GB   = [75,76,84]                   # guard alone
MC   = [72,65,71]                   # + recover+decode amplifier
MCRG = [43,43,58]                   # + reguard layer
MC_OR   = [64,59,59.5]              # benign over-refusal %, avg(text,image), mc
MCRG_OR = [84,80.5,86.5]            #                                        mc+reguard

# ---- DATA (InternVL3-8B, gpt-5-mini, n=100) — same 3 guards, generalization ----
FLOOR2 = 91
GB2   = [81,81,90]
MC2   = [63,69,67]
MCRG2 = [48,56,65]
MC_OR2   = [84,80,82]
MCRG_OR2 = [90,86,92]

# ---- Fig 1: ensemble ASR grouped bars ----
fig, ax = plt.subplots(figsize=(3.5,2.6))
x = np.arange(len(GUARDS)); w = 0.26
ax.axhline(FLOOR, ls='--', color=OI[7], lw=1)
ax.text(len(GUARDS)-0.5, FLOOR+1, 'no defense (89)', ha='right', va='bottom', fontsize=6, color=OI[7])
ax.bar(x-w, GB,   w, label='guard alone',            color=OI[1])
ax.bar(x,   MC,   w, label='+ amplifier',            color=OI[0])
ax.bar(x+w, MCRG, w, label='+ amplifier + reguard',  color=OI[2])
ax.set_xticks(x); ax.set_xticklabels(GUARDS)
ax.set_ylabel('Ensemble attack-success rate (%)'); ax.set_ylim(0,100)
ax.legend(frameon=False, fontsize=6, loc='lower left', ncol=1)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
fig.tight_layout(); fig.savefig(FIGS+"/ensemble_bars.pdf"); fig.savefig(FIGS+"/ensemble_bars.png", dpi=300)

# ---- Fig 2: safety-utility tradeoff frontier (BOTH models) ----
from matplotlib.lines import Line2D
fig, ax = plt.subplots(figsize=(3.5,3.0))
def plot_model(MCv, MCRGv, ORv, ORrgv, m_mc, m_rg, ls):
    for i in range(len(GUARDS)):
        ax.annotate('', xy=(ORrgv[i],MCRGv[i]), xytext=(ORv[i],MCv[i]),
                    arrowprops=dict(arrowstyle='->', color=OI[i], lw=1.2, alpha=0.85, linestyle=ls))
        ax.scatter(ORv[i],   MCv[i],   facecolors='none', edgecolors=OI[i], marker=m_mc, s=34, zorder=3, lw=1.3)
        ax.scatter(ORrgv[i], MCRGv[i], color=OI[i],       marker=m_rg, s=34, zorder=3)
plot_model(MC,  MCRG,  MC_OR,  MCRG_OR,  'o', 's', '-')    # Qwen2.5-VL
plot_model(MC2, MCRG2, MC_OR2, MCRG_OR2, '^', 'D', '--')   # InternVL3
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
