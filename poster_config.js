/* ===========================================================================
   POSTER CONTENT — this is the only file you need to edit.
   ---------------------------------------------------------------------------
   Everything on the poster comes from the POSTER object below. Change text
   here, save, reload poster.html.

   Three conventions worth knowing:

     * Any string containing TODO renders with a loud yellow highlight, so an
       unfinished field cannot be printed by accident. Search for TODO to find
       everything still outstanding.

     * Body text is HTML. <b>, <i>, <sub>, <sup> and &nbsp; all work, and a
       literal < or & must be escaped. Greek letters are written directly as
       Unicode (Ω, σ, δ, ×).

     * Maths goes between dollar signs, written as a small subset of LaTeX:

           "learns $p(Ω_m, σ_8 | s)$ from the summary $s$"

       _ and ^ subscript and superscript (brace anything longer than one
       character: $b_{s^2}$), \\name gives Greek and the operators, and
       \\text{...} sets a word upright. Variables come out italic and spacing
       follows TeX, so $z = 1$ and $z=1$ are the same. Greek is easier typed
       straight in as Unicode -- $Ω_m$ and $\\Omega_m$ are the same thing --
       and note that a backslash in a JS string has to be DOUBLED.

       A \\command it doesn't know, and a $ you forgot to close, come out
       highlighted like a TODO instead of printing wrong.

       Everything below takes maths except the labels drawn inside the two
       SVGs -- approaches[].stages and the cost chart -- where a $ would
       print literally. Full syntax: see mathHTML() in poster.html.

     * KEEP IT SHORT. The sheet is a fixed 36 in and clips what does not fit.
       A maroon banner warns you on screen if you overrun. Each block below
       carries a rough budget; treat them as real limits, not suggestions.

   The three approach columns are an array. To add WST and bispectrum columns
   later, append entries to POSTER.approaches — the band re-flows on its own.

   Type sizes live in POSTER.type at the BOTTOM of this file. Everything on the
   poster is sized from there, so you can retune the type without touching CSS.
   =========================================================================== */

const POSTER = {
  /* --- HEADER ---------------------------------------------------- ~3.3 in */
  meta: {
    /* Set on one line: .title uses white-space:nowrap, and --t-title in
       poster_style.css is sized so this fits the column beside the logos. If
       you lengthen it, drop --t-title a few points -- render.py reports the
       overrun, but a browser would clip it silently. */
    title: "Do we need field level inference for galaxy clustering?",

    subtitle:
      "Existing summaries still lose significant valuable information essential to " +
      "cosmological constraints.",

    // Superscripts index into `affiliations`, 1-based.
    // TODO: confirm the collaborator list and the order of names.
    authors: [
      { name: "Shrihan Agarwal", sups: [1, 2] },
      { name: "Georgios Valogiannis", sups: [1, 2, 3] },
      { name: "and Chihway Chang", sups: [1, 2] },
    ],

    affiliations: [
      "Department of Astronomy and Astrophysics, University of Chicago",
      "Kavli Institute for Cosmological Physics, University of Chicago",
      "Department of Physics, Illinois State University",
    ],

    venue: "OpenSkAI 2026",

    // Logos run left-to-right at the right edge. `height` is in inches.
    // Sized to the height of the title block beside them: taller than this and
    // the header grows, pushing the whole sheet past 36 in. render.py reports
    // both that overflow and any ink that lands in the page margin.
    logos: [
      {
        src: "uchicagologo.png.webp",
        alt: "University of Chicago",
        height: 1.35,
      },
      { src: "skailogo.png", alt: "SkAI Institute", height: 1.45 },
    ],

    // Drawn at the LEFT end of the logo row, before the UChicago seal. `height`
    // is in inches and the image is assumed square; 1.35 matches the seal
    // beside it. Set `src` to null to drop it, or give it a `caption` string to
    // label it. Remember to add the file to SITE_FILES in publish_site.py --
    // that script refuses to run if the config points at something it would not
    // publish, so a forgotten asset fails loudly rather than 404ing live.
    // TODO: confirm what the QR links to (repo? paper? your site?).
    qr: { src: "qr.png", caption: null, height: 1.35 },

    footer:
      "SkAI is funded by the U.S. National Science Foundation and the " +
      "Simons Foundation. Computing on NCSA Delta and DeltaAI.",
  },

  /* --- BAND 1: the framing question ------------------------------ ~5.6 in */
  question: {
    eyebrow: "Motivation",
    heading: "Inferring cosmology from 3D galaxy density fields is expensive",

    // The lede is set larger and unjustified. One or two sentences, no more.
    lede: "Our galaxy fields have 2.1M parameters. DESI 5Y will be <b>600x</b> larger.",

    body: [
      "<b>Field level inference</b> (FLI) of cosmological parameters at DESI scales remains infeasible. So, we compress it; the field is typically summarized as a " +
        "<b>power spectrum</b>.",
      "But if you <i>could</i> do FLI, how much better would it be?",
      "Are there other summaries, like <b>wavelet scattering transforms</b> or the <b>bispectrum</b> " +
        "that can recover similar constraints to FLI?",
      "And is there another option: using neural networks to create a <b>learned summary</b> " +
        "that performs just as well?",
    ],

    box: "What is each summary's information-compute tradeoff?",

    /* `caption` is null, so no caption is drawn. Put a string back and it
       reappears under the figure; nothing else has to change. */
    figure: {
      src: "figures/density_fields.png",
      caption: null,
    },
  },

  /* --- BAND 1.5: the shared mock, as a fact strip ---------------- ~2.0 in
     The DATASET rule above the strip takes only `eyebrow`; `label` is the bold
     text inside the strip, to the left of the facts, and sets the strip's
     height at about three lines in a 3.1 in column.
     ---------------------------------------------------------------------- */
  setup: {
    eyebrow: "Dataset",
    label: "Small, yet realistic, mock galaxy fields",
    facts: [
      { k: "Box", v: "320 Mpc/h @ 2.5 Mpc/h res." },
      { k: "Redshift", v: "$z = 1$" },
      { k: "Evolution", v: "Particle Mesh" },
      { k: "Effects", v: "RSD · shot noise" },
      { k: "Bias", v: "$b_1\\, b_2\\, b_{s^2}\\, b_{∇^2}$" },
      { k: "Parameters", v: "$Ω_m, σ_8$" },
    ],
  },

  /* The rule over the approach columns. Same shape as every other band
     head: heading on the left, hairline, eyebrow at the right margin. */
  summarization: {
    eyebrow: "Summarization",
    heading: "",
  },

  /* --- BAND 2: the ladder of compression ------------------------- ~6.0 in
     `dim` is the big number at the top of each column — the size of the
     summary that analysis hands to the inference. That IS the ladder.
     `schematic` picks a drawing: "pk" | "cnn" | "fl" | null
     "pk" and "cnn" are hand-drawn SVG icons and take three `stages` captions.
     "fl" is two rendered cubes and takes two, plus `cubes` and `arrowLabel`.
     ---------------------------------------------------------------------- */

  /* The field the P(k) and CNN drawings start from: the real evolved field at
     z = 1, the same simulation and colour scale as the Full Field column's z1
     cube, so band 2 reads as one universe compressed three ways. Written by

         /home/node/.conda/envs/simple/bin/python figures/make_fl_cubes.py

     alongside the two cubes. The path lives here rather than in poster.html
     because build_artifact.py inlines image paths it finds in this file. */
  fieldTile: "figures/field_tile.png",

  approaches: [
    {
      id: "pk",
      name: "Power Spectrum",
      color: "#3b6fd6",
      dim: "5",
      dimLabel: "parameters",
      schematic: "pk",
      /* the three captions under the drawing, left to right */
      stages: ["field", "measure P(k)", "5 components"],
      body:
        "The power spectrum exceptionally captures the linear growth of matter," +
        " but <b>loses information</b> where gravity dominates: smaller scales." +
        " PCA further compresses, capturing 98% of variance.",
    },
    {
      id: "cnn",
      name: "CNN-Learned Summary",
      color: "#c8541a",
      dim: "64",
      dimLabel: "parameters",
      schematic: "cnn",
      /* the three captions under the drawing, left to right */
      stages: ["field", "conv blocks", "64 numbers", "regress"],
      body:
        "A 3D CNN trained on ~40,000 cosmological sims to regress $Ω_m, σ_8$: <b>learning relevant features.</b>" +
        " The learned summary is taken from the latent space mid-network, after the convolutional stage.",
    },
    {
      id: "fl",
      name: "Full Field",
      color: "#0f9b8e",
      dim: "2.1M",
      dimLabel: "parameters",
      schematic: "fl",
      /* Full Field's drawing is two cubes of real simulation rather than an
         icon, so it takes `cubes` and only two captions. Both PNGs come from
         figures/make_fl_cubes.py -- see README for the two ways to run it.
         `arrowLabel` sits over the arrow between them and names what does the
         evolving. The body text below already makes the speed claim, so the
         label does not repeat it. Set it to "" to drop the label entirely. */
      stages: ["initial conditions", "evolved field, z = 1"],
      cubes: {
        ic: "figures/fl_cube_ic.png",
        z1: "figures/fl_cube_z1.png",
      },
      arrowLabel: "JaxPM",
      body:
        "<b>No summary at all.</b> The full fields are generated with the fast particle-mesh simulation JaxPM [1, 4], " +
        "which evolves the initial conditions to z = 1 in &lt;&nbsp;1 second, enabling 2.1M parameter sampling.",
    },
  ],

  /* --- The sampling aside ---------------------------------------- ~7.5 in
     Renders as the shaded column on the LEFT of the results band, beside the
     contour. It is a fixed-width column with no slack: about 20 lines at the
     current size. If you add much, drop --t-aside in poster_style.css.
     ---------------------------------------------------------------------- */
  sampling: {
    eyebrow: "Sampling",
    heading: "Summary &rarr; Constraint",

    paras: [
      "",
      "Both summaries go through <b>simulation-based inference</b> [3]. A normalizing " +
        "flow trained on ~40,000 mock fields learns $p(Ω_m, σ_8 | s)$ directly " +
        "from the compressed summary $s$, and is used to determine the constraint.",

      "Field level cannot use that trick: the initial field <i>is</i> the " +
        "parameter vector. All 2.1M dimensions are sampled jointly with " +
        "<b>MCLMC</b>&nbsp;[2], whose cost grows far more slowly with dimension " +
        "than HMC, and every gradient is a full 5-step JaxPM N-body (following [1]).",
    ],

    /* `note` — small print pinned to the floor of the panel — is unset, so
       none is drawn. Put a string back here and it reappears. */
  },

  /* --- BAND 3: results ------------------------------------------- ~8.2 in
     Numbers from compare/figures/fom_summary.csv, commit 8bbc622.
     ---------------------------------------------------------------------- */
  results: {
    eyebrow: "Measurement",
    heading: "Preliminary Results",
    figure: {
      // Currently the 180-dpi screen figure, soft at poster size. Run the
      // Poster export cell in compare_contours.ipynb, then point this at
      // figures/contours_poster.svg for a vector version.
      src: "figures/contours_poster.svg",
      caption: null, // see the note on POSTER.question.figure
      /* Stamped in the plot's top right corner. Set it to null to drop it --
         the contours are not final and the poster should say so on the figure
         itself, not only in the band heading. */
      tag: "Preliminary",
    },

    // The headline. These are the FoM ratios, repeated big under the figure.
    stats: [
      { value: "17%", label: "power spectrum", color: "#3b6fd6" },
      { value: "35%", label: "learned summary", color: "#c8541a" },
      { value: "100%", label: "field level", color: "#0f9b8e" },
    ],
    statsCaption: "of the field-level figure of merit",

    /* The discussion beside the contour. `lede` is the one-line claim;
       `bullets` are the points under it, drawn as a list; `note` is the small
       print at the floor of the column. Wrap a figure in <span class="c-pk">,
       <span class="c-cnn"> or <span class="c-fl"> and it takes the colour of
       that analysis's contour in the plot beside it.

       Five bullets is what the column holds at the current size. Each one
       should survive being read from four feet away, so lead with the bold
       phrase and keep the sentence after it to a line or two. */
    discussion: {
      lede: "Both summaries lose constraining power.",

      bullets: [
        "<b>One mock, three analyses.</b> All three condition on the same field; " +
          "what differs is the summarization level each is allowed to see.",

        '<b><span class="c-cnn">CNN</span> doubles FoM:</b> Compared to the <span class="c-pk">power spectrum</span>, indicating ' +
          "improvements possible for low computational cost.",

        '<b><span class="c-fl">FLI</span> significantly ahead:</b> Showing significant room for improved summarizations ' +
          "capturing more cosmological information. ",

        "<b>Alternative Summarizations:</b> Next steps include testing wavelet scattering transforms and bispectrum summaries. ",
        "<b>Preliminary Result:</b> Constraints may change with improvements in SBI training and more thorough analysis. ",
      ],

      note:
        "$\\text{FoM} = 1/\\sqrt{\\det C}$, inversely proportional to the 1-sig ellipse " +
        "area. Summaries limited to using scales $k < 0.8$ Mpc/h.",
    },

    /* NOT CURRENTLY RENDERED. Replaced by `discussion` above, which says the
       same thing in prose. The measured values are kept here as the record --
       re-append the table in poster.html's resultsBand() to show them again. */
    table: {
      columns: ["Analysis", "$Ω_m$", "$σ_8$", "FoM"],
      rows: [
        {
          label: "Power spectrum",
          om: "0.3168 ± 0.0265",
          s8: "0.8207 ± 0.0165",
          fom: "3,277",
          color: "#3b6fd6",
        },
        {
          label: "Learned summary",
          om: "0.2913 ± 0.0191",
          s8: "0.8171 ± 0.0091",
          fom: "6,502",
          color: "#c8541a",
        },
        {
          label: "Field level",
          om: "0.3007 ± 0.0103",
          s8: "0.8189 ± 0.0059",
          fom: "18,815",
          color: "#0f9b8e",
        },
      ],
      note:
        "$\\text{FoM} = 1/\\sqrt{\\det C}$, inversely proportional to the 68% ellipse " +
        "area. ± are marginal standard deviations. Truth: $Ω_m$ 0.3111, " +
        "$σ_8$ 0.8102. Field level: 6 of 8 chains, 5,760 samples.",
    },

    /* NOT CURRENTLY RENDERED. This was a panel in a third column; its width
       went to the contour instead. The text is kept so you can restore it --
       see the note in poster.html's resultsBand(). */
    takeaway: {
      heading: "Takeaway",
      body:
        "$P(k)$ recovers <b>17%</b> of the field-level figure of merit. A " +
        "learned 64-number summary doubles that to <b>35%</b> — and still " +
        "leaves a <b>factor of three</b> on the table.",
    },
  },

  /* --- BAND 4: cost versus gain ------------------------- NOT RENDERED ---
     The band was removed: hours on a 320 Mpc/h mock is not the cost that
     decides anything. The point is that field level does not scale to DESI
     volume, and this chart does not say that.

     Nothing here is lost. The chart still draws exactly as it did -- uncomment
     the costBand() call in poster.html's build block and it comes back, ~3.6 in
     tall. Set any value to a number to draw its bar; null renders TBD rather
     than silently plotting zero.
     ---------------------------------------------------------------------- */
  cost: {
    eyebrow: "The other axis",
    heading: "Cost versus gain",

    intro:
      "These are not the same kind of cost. A summary pays a large " +
      "<b>one-time</b> price for its simulation suite, and every posterior " +
      "after is nearly free. Field level pays the <b>full price every " +
      "time</b>.",

    // GPU-hours. null renders as TBD.
    // TODO: fill in the four nulls from the SLURM logs on Delta.
    series: [
      {
        label: "Power spectrum",
        color: "#3b6fd6",
        setup: 0.2,
        posterior: 0.5,
      },
      {
        label: "Learned summary",
        color: "#c8541a",
        setup: 2.5,
        posterior: 0.5,
      },
      { label: "Field level", color: "#0f9b8e", setup: 0, posterior: 30 },
    ],

    axisLabel: "GPU-hours (log scale)",

    // Decade ticks along the log axis, low to high. Eight of them, matching the
    // 0.01 to 100k span the chart draws.
    ticks: ["0.01", "0.1", "1", "10", "100", "1k", "10k", "100k"],

    unit: "h", // suffix on every measured bar
    tbdLabel: "TBD", // shown for a null, beside a dashed placeholder bar
    zeroLabel: "none", // shown for an exact 0, which a log axis cannot plot

    legend: [
      { key: "setup", label: "One-time setup" },
      { key: "posterior", label: "Per posterior" },
    ],

    note: "CNN training measured at 2h33m on one GH200 (cnn/slurm-3100084.out).",
  },

  /* --- FOOTER ---------------------------------------------------- ~2.4 in */
  future: {
    eyebrow: "Outlook",
    heading: "What comes next",
    items: [
      "<b>More rungs on the ladder.</b> Wavelet scattering and the bispectrum " +
        "slot in as two more columns.",

      "<b>Where the information lives.</b> Repeat against $k_{max}$ to " +
        "separate scale from nonlinearity.",

      "<b>Is the FoM gap worth it?</b> At what scale of problem should we switch " +
        "to a simpler summarization?",
    ],
  },

  references: [
    "Simon-Onfroy et al. 2025 — field-level benchmark and forward model.",
    "Robnik et al. 2022 — Microcanonical Langevin MC, the sampler used.",
    "Tejero-Cantero et al. 2020 — the sbi package, neural posterior estimation.",
    "Lanzieri et al. 2022 - JaxPM for fast N-Body Simulations",
    // TODO: check these three citations against your bibliography before printing.
  ],

  /* --- TYPE SIZES -----------------------------------------------------------
     Every piece of text on the poster is sized from here. Values are POINTS —
     write a plain number. A string is passed through as written, so "62.5pt"
     or "1.2in" also work if you want another unit.

     Delete a line and that item falls back to the default in poster_style.css;
     the whole block can be deleted safely. A name that isn't in the list below
     shows a maroon banner on screen (it never prints) rather than doing
     nothing quietly.

     Two of these are load-bearing and will bite:
       * `title` must keep the title on ONE line — it is set nowrap, and the
         sheet clips silently. 63pt is about the ceiling for the current title;
         render.py fails the build if it does not fit.
       * `subtitle` must keep the subtitle on one line; a second line pushes
         every band down ~0.37in and the sheet has ~0.3in to give.
     After changing anything here, re-run render.py — the sheet is a fixed 36in
     and a size raised by two points can push the footer off the bottom.
     ---------------------------------------------------------------------- */
  type: {
    /* header */
    title: 63,
    subtitle: 21.5,
    author: 28,
    affil: 15,
    qrCaption: 9.4, // the caption under a QR code, if you set one

    /* used by every band */
    eyebrow: 19, // the small caps label at the right of a band rule
    bandHeading: 30, // "Cost versus gain", "[PRELIMINARY] Results", ...
    lede: 25, // the maroon opening line of a band
    body: 25, // ordinary paragraphs
    callout: 27, // the boxed question in band 1
    figureCaption: 20, // only shows if you give a figure a caption
    figureTag: 21, // the corner stamp, e.g. "Preliminary" on the contour
    note: 19, // small print under a column

    /* the fact strip under band 1 */
    factLabel: 26, // "Small, yet realistic, mock galaxy fields"
    factKey: 16, // BOX, REDSHIFT, EVOLUTION, ...
    factValue: 23, // 320 Mpc/h @ 2.5 Mpc/h res., z = 1, ...

    /* the three approach columns */
    approachDim: 56, // the big 5 / 64* / 2.1M
    approachDimLabel: 20, // "parameters" beside it
    approachName: 31, // "Power Spectrum", "Full Field", ...
    approachBody: 23,

    /* the results band */
    asideHeading: 27, // "How each posterior is drawn"
    asideBody: 20,
    discussionLede: 28, // "The three posteriors nest..."
    discussionBody: 23,
    statValue: 48, // 17% / 35% / 100%
    statLabel: 15, // POWER SPECTRUM, LEARNED SUMMARY, FIELD LEVEL

    /* cost band and footer */
    costLegend: 20,
    futureItem: 20,
    reference: 17,
    colophon: 15,

    table: 25, // the numbers table, not currently rendered

    /* Text drawn inside the two SVGs. These are NOT points: they are viewBox
       units that scale with the drawing, about 0.8pt each in a schematic and
       0.72pt each in the cost chart. */
    svg: {
      schematicCaption: 17, // field / k-shells / 5 components
      costTick: 19, // 0.01, 0.1, 1, 10, ... along the axis
      costValue: 19, // "2.55 h", "TBD", "none" at the end of a bar
      costRowLabel: 21, // Power spectrum / Learned summary / Field level
      costAxis: 20, // "GPU-hours (log scale)"
    },
  },
};
