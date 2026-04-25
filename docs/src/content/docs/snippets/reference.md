--- 
title: Snippets References
description: A general reference for the snippets that txtr has built-in (not exhaustive)
--- 

This is not every single bundled snippet, but it covers the main groups that you will probably use regularly (for the more niche snippets, read the snippets menu via `:snips`). 

## Auto-expand symbols

| Trigger | Expands to |
| --- | --- |
| `//` | `\frac{...}{...}` |
| `^^` | `^{...}` |
| `__` | `_{...}` |
| `!=` | `\neq` |
| `<=` | `\leq` |
| `>=` | `\geq` | 
| `~=` | `\approx` | 
| `=>` | `\Rightarrow` | 
| `->` | `\rightarrow` | 
| `<-` | `\leftarrow` |
| `<=>` | `\LeftRightarrow` | 
| `...` | `\ldots` | 
| `**` | `\cdot` |

## Greek letters

Lowercase forms use `@` plus a letter, for example:

- `@a` --> `\alpha`
- `@b` --> `\beta`
- `@g` --> `\gamma`
- `@d` --> `\delta`
- `@t` --> `\theta`
- `@l` --> `\lambda`
- `@p` --> `\pi`
- `@s` --> `\sigma`
- `@w` --> `\omega`

Upperc case forms are also included:


- `@G` --> `\Gamma`
- `@D` --> `\Delta`
- `@S` --> `\Sigma`
- `@L` --> `\Lambda`
- `@O` --> `\Omega`
- `@T` --> `\Theta`


## Common writing helpers 

These are [tab-triggered](/snippets/overview). 

| Trigger | Expands to |
| --- | --- | 
| `cite` | `\cite{...}` |
| `ref` | `\ref{...}` |
| `erer` | `\eqref{...}` |
| `lab` | `\label{...}` |
| `em` | `\emph{...}` |
| `bf` | `\texbf{...}` |

## Math commands

Inside math mode, many of these also auto-expand as you type when `snippets.math_mode_snippets = true`.

| Trigger | Expands to |
| --- | --- | 
| `sq` | `\sqrt{...}` |
| `vec` | `\vec{...}` |
| `hat` | `\hat{...}` |
| `bar` | `\bar{...}` |
| `ovl` | `\overline{...}` |
| `lim` | `\lim_{... \to ...}` |
| `sum` | `\sum{...}^{....}` |
| `prod` | `\prod_{...}^{...}` |
| `int` | `\int_{...}^{...} ... \, d....` |

## Environments

All triggers below expand to something of the form:
```latex
\begin{...}

\end{...} % this is placed here automatically
```

| Trigger | Expands to |
| --- | --- | 
| `eq` | `equation` |
| `ali` | `align` |
| `gat` | `gather` |
| `mlt` | `multiline` |
| `cas` | `cases` |
| `mat` | `pmatrix` |
| `itm` | `itemize` |
| `enu` | `enumerate` |
| `fig` | `figure` |



## Templates 
| Trigger | Expands to |
| --- | --- | 
| `doc` | `basic article document` |
| `beamer` | `beamer presentation skeleton` |
| `rep` | `report skeleton` |

If you want the exact source for every bunlde snippet, look in `texitor/latex/snippets.toml` of the txtr source code, or the seeded `~/.config/txtr/snippets.toml`.

Happy snipping !
