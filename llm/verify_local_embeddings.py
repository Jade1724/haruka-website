import asyncio

from mecha_llm.embeddings_local import embed_texts


async def main() -> None:
    # 1. Determinism + width + normalization.
    (a1,) = await embed_texts(["hello world"])
    (a2,) = await embed_texts(["hello world"])
    assert a1 == a2, "same input must give identical vectors"
    assert len(a1) == 384, f"expected 384 dims, got {len(a1)}"
    norm = sum(x * x for x in a1) ** 0.5
    assert abs(norm - 1.0) < 1e-3, f"expected unit norm, got {norm}"

    # 2. Similar pair scores closer than a dissimilar pair (cosine distance).
    def cos_dist(u, v):
        return 1.0 - sum(x * y for x, y in zip(u, v))  # unit vectors

    cat, kitten, tax = await embed_texts(
        ["a small domestic cat", "a tiny kitten", "quarterly tax law"]
    )
    close, far = cos_dist(cat, kitten), cos_dist(cat, tax)
    assert close < far, f"{close=} should be < {far=}"

    print(f"OK — 384 dims, unit norm, similar={close:.3f} < dissimilar={far:.3f}")


asyncio.run(main())
