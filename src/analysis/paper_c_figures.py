"""Paper C result figures — ensemble bars + safety-utility tradeoff frontier.

⚠️ STALENESS DEFECT, FOUND AND FIXED 2026-08-07. This file held a HARDCODED data block
carrying PRE-AUDIT numbers. The method-fidelity audit (`b266892`) rebuilt `code_attack` and
`ir_figstep` and Table 1 was recomputed on the post-fix cells on 2026-08-06 — but nothing
recomputed the FIGURES, so both of them plotted a grid the paper no longer reports (Qwen
gb WildGuard 75 against Table 1's 77, +rg Qwen3Guard 43 against 50, GuardReasoner 58 against
63). A hardcoded table cannot fail, which is why `verify()` now exists: it rebuilds every
entered ASR from the data through the shared selector and RAISES on drift. Same defect class
and same remedy as `paper_c_pareto.py`.

ASR constants are transcribed from `tab:reguard` in the AIA paper and machine-checked by
`verify()`.

⚠️ SECOND STALENESS DEFECT, 2026-08-21 — the unchecked half is the half that rotted.
The note that used to stand here said the over-refusal constants were transcribed and
"NOT machine-checked". They then stayed on the two-category benign slice (OR-Bench-Hard
0-99 in file order = 72 deception + 28 harassment) for weeks after the category-balanced
n=300 draw was taken to be the paper's better estimate. cspaper review 5 con 5 found it.
The fix was to DERIVE over-refusal at plot time rather than transcribe it a second time.

⚠️ INSTRUMENT DEFECT IN THE BALANCED DRAW, FOUND SAME DAY (2026-08-21) — READ BEFORE
CHOOSING AN AXIS. The category-balanced benign draw is NOT interchangeable with the
two-category one, because its IMAGE channel was rendered with a different flag.
`ir_plain` takes `keep_text`, which decides whether the request also stays in the TEXT
field beside the image. It DEFAULTS TO TRUE. Every benign render in this paper passes
`keep_text: false` explicitly (`render_n100.yaml`, `heldout_stage1_render.yaml`,
`ensemble_benign_render.yaml`, `orbench_render.yaml`) so that the payload leaves the text
channel entirely — the same delivery as the harmful image renders, which is what makes the
attack and benign sides of `tab:viewprice` commensurable. `benign_stratified_s1.yaml`
OMITTED the flag, so the balanced benign image channel kept the request in the text field
and the text-only guards could read it. Measured consequence: on the two-category draw a
text-only guard blocks EXACTLY 0.0% of benign images (blind, as intended); on the balanced
draw the same guard blocks 74%. That is not a category effect and cannot be — a blind guard
cannot be made sighted by changing which categories it is blind to. On the one channel where
the instrument IS identical (text), balancing moves guard-alone blocking by ~4 points.

So the balanced draw currently measures RE-RENDERING (guard already saw the text) where the
two-category draw measures RESTORING A VIEW (guard saw nothing). The sign flip that the
2026-08-09 reframe attributed to category coverage is the flag, not the categories. Until
the image channel is re-run with `keep_text: false`, the instrument-matched axis is the
two-category one and it is the DEFAULT here. `--axis balanced` is available for the
diagnostic, and prints the caveat every time.

Regenerate with `.venv/bin/python -m src.analysis.paper_c_figures [--axis 2cat|balanced]`
(runs verify() first).
Uses the scientific-visualization skill's publication style."""
import sys, os
SKILL = "/Users/haoyu/.claude/skills/scientific-visualization"
sys.path.insert(0, SKILL + "/scripts"); sys.path.insert(0, SKILL + "/assets")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.lines import Line2D
OI = ['#E69F00','#56B4E9','#009E73','#F0E442','#0072B2','#D55E00','#CC79A7','#000000']
FIGS = "paper/as-3/aaai_2027_main/aaai_main_latex/figs"
# The live submission is the AI-Alignment track version; figures must land in BOTH
# trees or a regeneration silently updates only the retired main-track copy.
FIGS_ALT = "paper/as-3/aaai_2027_ai_alignment/aaai_aia_latex/figs"


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

def plot_model(GBv, MCv, MCRGv, ORgbv, ORv, ORrgv, m_mc, m_rg, ls, ax, errors=True):
    """One target's guard-alone -> amplifier -> +reguard trajectory.

    The guard-alone leg was added 2026-08-07 on a reviewer's ask: Table 1 shows the
    gb->mc transition is often qualitatively different from mc->+rg (it can move the
    wrong way), and a figure that starts at mc invites the reader to credit the whole
    displacement to the amplifier.

    2026-08-08: its WEIGHT is now equal to the reguard leg. It was originally drawn
    faint because under the paper's earlier framing mc->+rg was the contrast that
    mattered -- the one surviving correction. Under the view account the gb->mc leg IS
    mechanism A (adding a view the guard could not read), so a faint dotted leg put the
    paper's central mechanism in the visual background. The two legs stay distinguishable
    by LINESTYLE (dotted = adding a view, solid = closing the residual) rather than by
    prominence, which is the honest encoding: they are different mechanisms, not a main
    effect and a footnote.

    `errors=True` draws Wilson 95% whiskers on both axes of every point (review 18's
    presentation ask: "plotting points without uncertainty visually overstates how
    precisely the frontier is located"). They are deliberately thin, capless and
    semi-transparent, drawn UNDER the markers -- 20 whiskers in a 3.5in panel is the
    most uncertainty this figure can carry and stay readable. Note the two axes have
    different n: ensemble ASR is over 100 behaviors, over-refusal is the average of a
    100-prompt text channel and a 100-prompt image channel, so n=200.
    """
    for i in range(len(MCv)):
        ax.annotate('', xy=(ORv[i], MCv[i]), xytext=(ORgbv[i], GBv[i]),
                    arrowprops=dict(arrowstyle='->', color=OI[i], lw=1.2, alpha=0.85,
                                    linestyle=':'))
        ax.scatter(ORgbv[i], GBv[i], facecolors='none', edgecolors=OI[i], marker='^',
                   s=34, zorder=3, lw=1.3)
        if errors:
            for xv, yv in ((ORv[i], MCv[i]), (ORrgv[i], MCRGv[i])):
                ax.errorbar(xv, yv,
                            yerr=wilson_err([yv], n=100), xerr=wilson_err([xv], n=OR_N),
                            fmt='none', ecolor=OI[i], elinewidth=0.6, alpha=0.32,
                            capsize=0, zorder=1)
        ax.annotate('', xy=(ORrgv[i],MCRGv[i]), xytext=(ORv[i],MCv[i]),
                    arrowprops=dict(arrowstyle='->', color=OI[i], lw=1.2, alpha=0.85, linestyle=ls))
        ax.scatter(ORv[i],   MCv[i],   facecolors='none', edgecolors=OI[i], marker=m_mc, s=34, zorder=3, lw=1.3)
        ax.scatter(ORrgv[i], MCRGv[i], color=OI[i],       marker=m_rg, s=34, zorder=3)

# ---- DATA (Qwen2.5-VL, gpt-5-mini, n=100) — all FIVE guards, POST-FIX (tab:reguard) ----
GUARDS = ['WildGuard','Qwen3Guard','GuardReasoner','LlamaGuard-3','ThinkGuard']
GUARD_KEY = {'WildGuard':'wildguard', 'Qwen3Guard':'qwen3guard_gen_8b',
             'GuardReasoner':'guardreasoner_vl_7b', 'LlamaGuard-3':'llama_guard_3_8b',
             'ThinkGuard':'thinkguard'}
FLOOR = 89                          # no_defense ensemble (guard-independent)
FLOOR_OR_2CAT = 26                  # RETIRED (2-category slice)
GB   = [77,75,84,66,79]             # guard alone
MC   = [68,68,71,78,81]             # + recover+decode amplifier
MCRG = [43,50,63,49,58]             # + reguard layer
GB_OR_2CAT   = [49,47,67,28,47]     # RETIRED axis (2-category slice), kept for the appendix
MC_OR_2CAT   = [64,59,60,28,45]     #   diagnostic only — see points_balanced() rationale
MCRG_OR_2CAT = [84,81,87,33,66]

# ---- DATA (InternVL3-8B, gpt-5-mini, n=100) — all FIVE guards, POST-FIX ----
# Not plotted (Fig 2 is deliberately Qwen-only, see below) but kept correct: a stale
# spare data block is how the Qwen block went stale in the first place.
FLOOR2 = 94
FLOOR_OR2_2CAT = 53
GB2   = [86,83,88,82,83]
MC2   = [70,76,76,81,81]
MCRG2 = [49,55,69,61,62]
GB_OR2_2CAT   = [70,69,81,54,67]
MC_OR2_2CAT   = [84,80,82,55,72]
MCRG_OR2_2CAT = [90,86,92,57,79]


# ---- LIVE over-refusal axis: CATEGORY-BALANCED (n=300 x 2 channels = 600 paired) ----
# Swapped 2026-08-21 (cspaper review 5 con 5 / Q1). The two-category slice above is
# OR-Bench-Hard 0-99 in file order, which the released file sorts by category: 72
# deception + 28 harassment, nothing else. The paper's own appendix calls it
# unrepresentative, so plotting the frontier on it while the balanced measurement sat in
# the appendix was indefensible. DERIVED, not transcribed -- the ASR half of this module
# needed a verify() because it was entered by hand; the utility half now has no second
# home to drift from, which is the defect class that produced this swap.
_B = None
def _over(target, guard, cond):
    global _B
    if _B is None:
        from src.analysis.paper_c_benign_stratified import balanced_overrefusal
        _B = balanced_overrefusal()
    return round(_B[(target, GUARD_KEY[guard], cond)], 1)

def _floor(target):
    global _B
    if _B is None:
        from src.analysis.paper_c_benign_stratified import balanced_overrefusal
        _B = balanced_overrefusal()
    return round(_B[(target, 'FLOOR', 'floor')], 1)

def load_balanced():
    """Fill the six live over-refusal series + both floors from the balanced draw."""
    global GB_OR, MC_OR, MCRG_OR, GB_OR2, MC_OR2, MCRG_OR2, FLOOR_OR, FLOOR_OR2, OR_N
    from src.analysis.paper_c_benign_stratified import scan, instrument_gate
    if not instrument_gate(scan()):
        raise SystemExit('load_balanced(): image channel contaminated (keep_text=True) — '
                         'run without --axis balanced, or re-run stage 1 with the flag.')
    q, i = 'qwen2_5_vl_7b', 'internvl3_8b'
    OR_N = 600
    GB_OR    = [_over(q, g, 'gb') for g in GUARDS]
    MC_OR    = [_over(q, g, 'mc') for g in GUARDS]
    MCRG_OR  = [_over(q, g, 'rg') for g in GUARDS]
    GB_OR2   = [_over(i, g, 'gb') for g in GUARDS]
    MC_OR2   = [_over(i, g, 'mc') for g in GUARDS]
    MCRG_OR2 = [_over(i, g, 'rg') for g in GUARDS]
    FLOOR_OR, FLOOR_OR2 = _floor(q), _floor(i)
    print(f'balanced axis loaded: Qwen floor {FLOOR_OR}, InternVL3 floor {FLOOR_OR2}')
    print('  ⚠ BALANCED AXIS: its image channel was rendered with keep_text=True, so the '
          'guard reads\n    the request in the text field and no view is being restored. '
          'Not commensurable with\n    the attack axis or with tab:viewprice. Diagnostic '
          'only until the keep_text=false re-run.')


def load_2cat():
    """The INSTRUMENT-MATCHED axis: two-category slice, benign images rendered with
    keep_text=false so the text-only guards are blind to them exactly as they are to the
    harmful renders. Category-unrepresentative (72 deception / 28 harassment) — that is the
    known and declared limitation — but it prices the same transition the attack axis does."""
    global GB_OR, MC_OR, MCRG_OR, GB_OR2, MC_OR2, MCRG_OR2, FLOOR_OR, FLOOR_OR2, OR_N
    GB_OR, MC_OR, MCRG_OR = GB_OR_2CAT, MC_OR_2CAT, MCRG_OR_2CAT
    GB_OR2, MC_OR2, MCRG_OR2 = GB_OR2_2CAT, MC_OR2_2CAT, MCRG_OR2_2CAT
    FLOOR_OR, FLOOR_OR2 = FLOOR_OR_2CAT, FLOOR_OR2_2CAT
    OR_N = 200
    print(f'two-category (instrument-matched) axis loaded: Qwen floor {FLOOR_OR}, '
          f'InternVL3 floor {FLOOR_OR2}, n={OR_N}')

GB_OR = MC_OR = MCRG_OR = GB_OR2 = MC_OR2 = MCRG_OR2 = None
FLOOR_OR = FLOOR_OR2 = None
OR_N = 200          # paired benign prompts behind the utility axis; 600 on the balanced draw


def verify() -> None:
    """Rebuild every entered ASR from the data and RAISE on mismatch.

    The over-refusal series are not covered (different benchmark tree); they are
    transcribed from the same table and move only if that table is rebuilt.
    """
    from src.analysis import paper_c_select as S
    bad = []
    for target, series in (('qwen2_5_vl_7b', {'gb': GB, 'mc': MC, 'rg': MCRG}),
                           ('internvl3_8b', {'gb': GB2, 'mc': MC2, 'rg': MCRG2})):
        sel = S.scan()
        for cond, vals in series.items():
            for g, entered in zip(GUARDS, vals):
                found, missing = S.postfix_dirs(sel, target, GUARD_KEY[g], cond)
                S.require_full(found, missing, f'{target}/{g}/{cond}')
                actual = round(S.rate(S.ens(found.values())))
                if actual != entered:
                    bad.append(f'{target} {g} {cond}: entered {entered}, data says {actual}')
    if bad:
        raise SystemExit('🔴 FIGURE DATA IS STALE — regenerating would plot a grid the '
                         'paper no longer reports:\n  ' + '\n  '.join(bad))
    print('verify: all 30 entered ASR values reproduce from the data.')


def main() -> None:
    try:
        from style_presets import apply_publication_style; apply_publication_style('default')
    except Exception as e:
        print("style preset fallback:", e)
        plt.rcParams.update({'font.size':8,'axes.labelsize':9,'font.family':'sans-serif'})
    verify()
    axis = 'balanced' if '--axis' in sys.argv and 'balanced' in sys.argv else '2cat'
    (load_balanced if axis == 'balanced' else load_2cat)()
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
    plot_model(GB, MC, MCRG, GB_OR, MC_OR, MCRG_OR, 'o', 's', '-', ax)  # Qwen2.5-VL (5 guards)
    ax.set_xlabel('Benign over-refusal (%)  →  worse utility')
    ax.set_ylabel('Ensemble ASR (%)  →  worse safety')

    # Label text is DARKENED per guard: the Okabe-Ito yellow (#F0E442) is fine as a
    # marker edge but unreadable as small bold text on white.
    def dark(hexc, f=0.62):
        r,g,b = (int(hexc[i:i+2],16) for i in (1,3,5))
        return '#%02x%02x%02x' % (int(r*f), int(g*f), int(b*f))

    # Per-guard label offsets (points), hand-placed; re-placed 2026-08-21 for the
    # balanced axis, which moves every amplifier marker left. On this axis WildGuard
    # (69.8,68) and Qwen3Guard (70.0,68) land 0.2 points apart -- their markers genuinely
    # overlap, which is data and not a plotting artifact, so the labels separate
    # vertically rather than the markers being nudged apart to fake resolution. The
    # caption says so.
    # Placement follows the AXIS, because the two axes put the markers in different
    # places. 2cat is the default (instrument-matched); the balanced offsets are the ones
    # tuned on 2026-08-21 before the instrument defect was found.
    # LlamaGuard-3 (28,79) and ThinkGuard (45,77) are close enough in y on the 2cat axis
    # that a right-extending LlamaGuard label collides with ThinkGuard's; LlamaGuard goes
    # left there.
    OFF = ({'WildGuard':(11,3), 'Qwen3Guard':(-4,-14), 'GuardReasoner':(-54,4),
            'LlamaGuard-3':(-16,10), 'ThinkGuard':(-12,9)} if OR_N == 600 else
           {'WildGuard':(9,-1), 'Qwen3Guard':(-7,-12), 'GuardReasoner':(-38,5),
            'LlamaGuard-3':(-14,10), 'ThinkGuard':(2,7)})
    for i, g in enumerate(GUARDS):
        ax.annotate(g, xy=(MC_OR[i], MC[i]), xytext=OFF[g], textcoords='offset points',
                    fontsize=6.8, color=dark(OI[i]), fontweight='bold', zorder=5)

    # Bottom-LEFT: the only quadrant no series occupies (everything runs down-right).
    ax.text(0.02, 0.03,
            'Qwen2.5-VL-7B\nopen triangle: guard alone  >  open circle: + amplifier\n>  filled square: + amplifier + reguard',
            transform=ax.transAxes, fontsize=6.4, ha='left', va='bottom', color='0.30', linespacing=1.4)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=7.5)
    ax.set_ylim(33, 92)   # widened again for the guard-alone points (up to 84 ASR)
    fig.tight_layout(); save(fig, "tradeoff_frontier")
    print("wrote:", os.listdir(FIGS))


if __name__ == "__main__":
    main()
