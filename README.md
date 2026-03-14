# Omics Figure Atlas

This repository contains a static GitHub Pages-ready showcase for bioinformatics figures. Each card is backed by:

- a metadata entry in `assets/figures.js`
- a small demo dataset in `content/datasets/`
- a browser-side renderer in `content/renderers/`

## Local preview

Serve the folder over HTTP so module imports and `fetch()` calls work:

```powershell
cd E:\workdir\bioinformatics-board
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/`.

## Add your own figure

1. Put a small test dataset in `content/datasets/`.
2. Create a renderer module in `content/renderers/` that exports:

   ```javascript
   export async function renderFigure(container, dataset, context) {
     const { Plotly } = context;
     await Plotly.newPlot(container, [/* traces */], {/* layout */}, { responsive: true });
   }
   ```

3. Register the figure in `assets/figures.js`.

If your original analysis code is in R or Python, keep a lightweight browser renderer for the public demo and point `codePath` to the original `.R` or `.py` file if you want to display that source instead.
