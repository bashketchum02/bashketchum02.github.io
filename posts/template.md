# Post Template

This is a template showing how to write blog posts in markdown. Save your posts as `.md` files in the `posts/` directory.

## Front Matter

Each post should start with YAML front matter:

```yaml
---
title: Your Post Title
date: 2026-02-08
category: MLOps
tags: [feature-engineering, infrastructure]
excerpt: A brief description of your post.
---
```

## Writing Content

### Text Formatting

Regular paragraphs are just plain text. You can use **bold** and *italic* text.

### Code Blocks

Use triple backticks with the language name:

```python
def train_model(X, y, epochs=100):
    """Train a simple model."""
    model = create_model()
    for epoch in range(epochs):
        loss = model.fit(X, y)
        print(f"Epoch {epoch}: loss={loss:.4f}")
    return model
```

Inline code uses single backticks: `model.predict(X)`.

### LaTeX Equations

Inline math uses single dollar signs: $f(x) = x^2 + 2x + 1$.

Display math uses double dollar signs:

$$
\mathcal{L}(\theta) = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(\hat{y}_i) + (1-y_i) \log(1-\hat{y}_i) \right]
$$

More complex equations:

$$
\nabla_\theta J(\theta) = \mathbb{E}_{\pi_\theta} \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t|s_t) \cdot R_t \right]
$$

### Images

```markdown
![Alt text](../images/your-image.png)
```

For figures with captions, the renderer will automatically wrap them:

```markdown
![Figure 1: Architecture diagram](../images/architecture.png)
```

### Lists

Unordered:
- First item
- Second item
- Third item

Ordered:
1. First step
2. Second step
3. Third step

### Blockquotes

> This is a blockquote. Use it for important quotes or callouts.

### Callouts

Use special syntax for callouts:

> [!NOTE]
> This is a note callout.

> [!WARNING]
> This is a warning callout.

> [!INFO]
> This is an info callout.

### Tables

| Model | Accuracy | Latency |
|-------|----------|---------|
| BERT  | 92.3%    | 45ms    |
| GPT-2 | 91.8%    | 38ms    |
| T5    | 93.1%    | 52ms    |

### Links

[Link text](https://example.com)

External links automatically open in new tabs.

---

## Converting Markdown to HTML

Use the build script or markdown renderer to convert `.md` files to `.html`:

```bash
python build.py
```

This will process all markdown files and generate the corresponding HTML pages.
