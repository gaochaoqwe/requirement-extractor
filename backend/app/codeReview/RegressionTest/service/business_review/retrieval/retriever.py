from typing import List, Dict, Any, Tuple
import math
from collections import Counter, defaultdict


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    # 简化分词：按非字母数字切分，转小写
    import re
    return [t.lower() for t in re.split(r"[^A-Za-z0-9_]+", text) if t]


class BM25:
    def __init__(self, docs: List[List[str]], k1: float = 1.5, b: float = 0.75, delta: float = 1.0):
        self.docs = docs
        self.N = len(docs)
        self.k1 = k1
        self.b = b
        self.delta = delta
        self.avgdl = sum(len(d) for d in docs) / (self.N or 1)
        self.df = Counter()
        for d in docs:
            for t in set(d):
                self.df[t] += 1
        self.doc_tf = [Counter(d) for d in docs]
        self.doc_len = [len(d) for d in docs]

    def _idf(self, t: str) -> float:
        # Robertson-Walker IDF
        dft = self.df.get(t, 0)
        return math.log((self.N + 1) / (dft + 0.5))

    def score(self, q: List[str], idx: int) -> float:
        score = 0.0
        tf = self.doc_tf[idx]
        dl = self.doc_len[idx]
        for t in q:
            if t not in tf:
                continue
            idf = self._idf(t)
            tf_td = tf[t]
            denom = tf_td + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            score += idf * ((self.k1 + 1) * tf_td / (denom + 1e-9) + self.delta)
        return score

    def rank(self, q: List[str], topk: int = 10) -> List[Tuple[int, float]]:
        scores = [(i, self.score(q, i)) for i in range(self.N)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:topk]


def build_bm25_index(corpus: List[Dict[str, Any]], field: str) -> Tuple[BM25, List[Dict[str, Any]]]:
    tokenized = [_tokenize(doc.get(field, "")) for doc in corpus]
    return BM25(tokenized), corpus


def search(corpus: List[Dict[str, Any]], field: str, query: str, topk: int = 10) -> List[Dict[str, Any]]:
    bm25, docs = build_bm25_index(corpus, field)
    q = _tokenize(query)
    results = bm25.rank(q, topk=topk)
    return [docs[i] for i, _ in results]


def two_stage_retrieve(files_docs: List[Dict[str, Any]],
                       funcs_docs: List[Dict[str, Any]],
                       query: str,
                       file_topk: int = 10,
                       func_topk: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    """两阶段检索：先文件摘要，再限定到这些文件的函数级。"""
    top_files = search(files_docs, field="summary", query=query, topk=file_topk)
    file_set = {f.get("file") for f in top_files}
    narrowed_funcs = [d for d in funcs_docs if d.get("file") in file_set]
    top_funcs = search(narrowed_funcs, field="text", query=query, topk=func_topk)
    return {"files": top_files, "functions": top_funcs} 