export const siteMeta = {
  title: "Omics Figure Atlas",
  subtitle: "Interactive showcase for bioinformatics plots across omics workflows.",
  intro:
    "Organize your figures by analysis type, attach compact demo datasets, and let visitors inspect the code that rebuilds each visualization directly in the browser.",
  callouts: ["GitHub Pages ready", "Live Plotly previews", "Code and data attached"],
};

export const figureCatalog = [
  {
    id: "rnaseq-volcano",
    title: "RNA-seq Volcano Plot",
    figureType: "Volcano plot",
    analysisType: "Differential Expression",
    omicsDomain: "Transcriptomics",
    summary:
      "A compact differential expression view that highlights genes crossing fold-change and adjusted p-value thresholds.",
    narrative:
      "Use this slot to describe the comparison, normalization method, statistical framework, and the biological takeaway you want visitors to notice first.",
    caption:
      "Genes with |log2FC| >= 1 and adjusted p-value < 0.05 are highlighted and labeled when strongly significant.",
    tags: ["RNA-seq", "DE analysis", "Tumor vs control"],
    notes: [
      "Good fit for bulk RNA-seq or pseudo-bulk single-cell contrasts.",
      "Synthetic dataset included so the public demo renders instantly.",
      "Replace the summary text with cohort size, method, and interpretation.",
    ],
    accent: "#0f8a83",
    datasetPath: "../content/datasets/volcano-demo.csv",
    datasetLabel: "volcano-demo.csv",
    rendererPath: "../content/renderers/volcano-plot.js",
    codePath: "../content/renderers/volcano-plot.js",
    codeLabel: "volcano-plot.js",
    codeLanguage: "javascript",
  },
  {
    id: "microbiome-pcoa",
    title: "Microbiome PCoA Separation",
    figureType: "Ordination scatter",
    analysisType: "Ordination",
    omicsDomain: "Microbiome",
    summary:
      "An ordination view for beta-diversity style results, grouped by cohort and labeled at the sample level.",
    narrative:
      "This works well for 16S or metagenomic community structure summaries where you want to communicate group-level separation without showing full distance matrices.",
    caption:
      "Samples are grouped by cohort and labeled individually to make the demo useful even with a tiny test dataset.",
    tags: ["16S", "PCoA", "Beta diversity"],
    notes: [
      "Useful for Bray-Curtis, UniFrac, or other distance-based ordinations.",
      "The live renderer groups traces by cohort automatically from the attached dataset.",
      "Add method notes here if you want to disclose distance metric and preprocessing.",
    ],
    accent: "#c45c31",
    datasetPath: "../content/datasets/pcoa-demo.csv",
    datasetLabel: "pcoa-demo.csv",
    rendererPath: "../content/renderers/pcoa-plot.js",
    codePath: "../content/renderers/pcoa-plot.js",
    codeLabel: "pcoa-plot.js",
    codeLanguage: "javascript",
  },
  {
    id: "proteomics-heatmap",
    title: "Proteomics Signature Heatmap",
    figureType: "Cluster heatmap",
    analysisType: "Feature Profiling",
    omicsDomain: "Proteomics",
    summary:
      "A heatmap panel for compact feature signatures, showing sample groups and z-scored intensities across proteins.",
    narrative:
      "Use this for proteomics, metabolomics, or integrated marker panels where a matrix view communicates coordinated signal patterns better than a univariate chart.",
    caption:
      "Rows represent signature features and columns represent samples; values are normalized z-scores for a small demo panel.",
    tags: ["Proteomics", "Heatmap", "Signature panel"],
    notes: [
      "The JSON format keeps matrix-based demos straightforward on static hosting.",
      "This pattern also works for pathway scores, phospho-signatures, and targeted marker panels.",
      "Keep demo matrices small so GitHub Pages stays fast.",
    ],
    accent: "#6f55b5",
    datasetPath: "../content/datasets/heatmap-demo.json",
    datasetLabel: "heatmap-demo.json",
    rendererPath: "../content/renderers/heatmap-plot.js",
    codePath: "../content/renderers/heatmap-plot.js",
    codeLabel: "heatmap-plot.js",
    codeLanguage: "javascript",
  },
];
