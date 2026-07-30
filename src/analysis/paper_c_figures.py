"""Paper C result figures — ensemble bars + safety-utility tradeoff frontier.
Numbers are the gpt-5-mini VALIDATED Qwen2.5-VL results (experiment_results.md §5-Guard Panel + §RQ4).
Regenerate with `python src/analysis/paper_c_figures.py`; add the InternVL3 2nd-model data to the DATA
block when gen2_internvl3 lands. Uses the scientific-visualization skill's publication style."""
import sys, os
SKILL = "/Users/haoyu/.claude/skills/scientific-visualization"
sys.path.insert(0, SKILL + "/scripts"); sys.path.insert(0, SKILL + "/assets")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.lines import Line2D
OI = ['#E69F00','#56B4E9','#009E73','#F0E442','#0072B2','#D55E00','#CC79A7','#000000']
FIGS = "paper/autoattack_defense/aaai_2027_main/aaai_main_latex/figs"
# The live submission is the AI-Alignment track version; figures must land in BOTH
# trees or a regeneration silently updates only the retired main-track copy.
FIGS_ALT = "paper/autoattack_defense/aaai_2027_ai_alignment/aaai_aia_latex/figs"


def save(fig, stem):
    for d in (FIGS, FIGS_ALT):
        if os.path.isdir(d):
            fig.savefig(f"{d}/{stem}.pdf")
            fig.savefig(f"{d}/{stem}.png", dpi=300)

def wilson_err(vals, n=100, z=1.96):
    """Asymmetric Wilson 95% CI half-widths (lower,upper) for yerr; matches tab:app-stats."""
    lo, hi = [], []
    for v in vals:
        p = v/100.0; d = 1 + z*z/n
        c = (p + z*z/(2*n))/d
        h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
        lo.append(v - (c-h)*100); hi.append((c+h)*100 - v)
    return np.array([lo, hi])

def plot_model(MCv, MCRGv, ORv, ORrgv, m_mc, m_rg, ls, ax, errors=True):
    """One target's amplifier -> +reguard arrows.

    `errors=True` draws Wilson 95% whiskers on both axes of every point (review 18's
    presentation ask: "plotting points without uncertainty visually overstates how
    precisely the frontier is located"). They are deliberately thin, capless and
    semi-transparent, drawn UNDER the markers -- 20 whiskers in a 3.5in panel is the
    most uncertainty this figure can carry and stay readable. Note the two axes have
    different n: ensemble ASR is over 100 behaviors, over-refusal is the average of a
    100-prompt text channel and a 100-prompt image channel, so n=200.
    """
    for i in range(len(MCv)):
        if errors:
            for xv, yv in ((ORv[i], MCv[i]), (ORrgv[i], MCRGv[i])):
                ax.errorbar(xv, yv,
                            yerr=wilson_err([yv], n=100), xerr=wilson_err([xv], n=200),
                            fmt='none', ecolor=OI[i], elinewidth=0.6, alpha=0.32,
                            capsize=0, zorder=1)
        ax.annotate('', xy=(ORrgv[i],MCRGv[i]), xytext=(ORv[i],MCv[i]),
                    arrowprops=dict(arrowstyle='->', color=OI[i], lw=1.2, alpha=0.85, linestyle=ls))
        ax.scatter(ORv[i],   MCv[i],   facecolors='none', edgecolors=OI[i], marker=m_mc, s=34, zorder=3, lw=1.3)
        ax.scatter(ORrgv[i], MCRGv[i], color=OI[i],       marker=m_rg, s=34, zorder=3)

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


def main() -> None:
    try:
        from style_presets import apply_publication_style; apply_publication_style('default')
    except Exception as e:
        print("style preset fallback:", e)
        plt.rcParams.update({'font.size':8,'axes.labelsize':9,'font.family':'sans-serif'})
    os.makedirs(FIGS, exist_ok=True)

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
    fig.tight_layout(); save(fig, "ensemble_bars")

    # ---- Fig 2: safety-utility tradeoff frontier (BOTH models) ----
    # NO LEGEND. Two reviewers independently asked for direct point labels instead
    # of a colour key ("annotating the specific guard names near each point would
    # make the frontier visualization self-contained"). The old version carried two
    # legends -- 5 guard entries + 2 model entries -- at 6pt inside a 3.5in panel,
    # which is what made it unreadable. Guard identity now sits next to the point;
    # the target model is named once per cluster. Legend entries: 7 -> 0.
    # QWEN-ONLY, deliberately. The InternVL3 series was 6 more markers + 3 arrows
    # landing in the already-crowded top-right, and it covered only 3 of the 5
    # guards -- which review 15 con 10 flagged as an inconsistency in the figure
    # ("the benign-utility component ... is only directly measured for three of
    # five guards on InternVL3"). Showing one COMPLETE panel removes both the
    # clutter and the partial-coverage objection; Table 1 carries both targets.
    fig, ax = plt.subplots(figsize=(3.5,2.95))
    plot_model(MC,  MCRG,  MC_OR,  MCRG_OR,  'o', 's', '-', ax)    # Qwen2.5-VL (5 guards)
    ax.set_xlabel('Benign over-refusal (%)  →  worse utility')
    ax.set_ylabel('Ensemble ASR (%)  →  worse safety')

    # Label text is DARKENED per guard: the Okabe-Ito yellow (#F0E442) is fine as a
    # marker edge but unreadable as small bold text on white.
    def dark(hexc, f=0.62):
        r,g,b = (int(hexc[i:i+2],16) for i in (1,3,5))
        return '#%02x%02x%02x' % (int(r*f), int(g*f), int(b*f))

    # Per-guard label offsets (points), hand-placed. The Qwen amplifier markers for
    # GuardReasoner (59.5,71) and WildGuard (64,72) are ~4.5 units apart at the same
    # height, so their labels are pushed to opposite sides; Qwen3Guard drops below.
    # LlamaGuard-3 (28,79) and ThinkGuard (45,77) are close enough in y that a
    # right-extending LlamaGuard label collides with ThinkGuard's; LlamaGuard goes
    # ABOVE its marker, ThinkGuard shifts right.
    OFF = {'WildGuard':(9,-1), 'Qwen3Guard':(-7,-12), 'GuardReasoner':(-38,5),
           'LlamaGuard-3':(-14,10), 'ThinkGuard':(2,7)}
    for i, g in enumerate(GUARDS):
        ax.annotate(g, xy=(MC_OR[i], MC[i]), xytext=OFF[g], textcoords='offset points',
                    fontsize=6.8, color=dark(OI[i]), fontweight='bold', zorder=5)

    # Bottom-LEFT: the only quadrant no series occupies (everything runs down-right).
    ax.text(0.02, 0.03, 'Qwen2.5-VL-7B\nopen → filled  =  amplifier → +reguard',
            transform=ax.transAxes, fontsize=6.4, ha='left', va='bottom', color='0.30', linespacing=1.4)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=7.5)
    ax.set_ylim(33, 90)   # widened for the Wilson whiskers added for review 18
    fig.tight_layout(); save(fig, "tradeoff_frontier")
    print("wrote:", os.listdir(FIGS))


if __name__ == "__main__":
    main()
