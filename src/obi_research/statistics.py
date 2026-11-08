"""Fixed-time block bootstrap for dependent observations (not IID intervals)."""
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, roc_auc_score


def metrics(y, probability):
    predicted=probability>=.5
    return dict(n=len(y), accuracy=float(accuracy_score(y,predicted)),
        balanced_accuracy=float(balanced_accuracy_score(y,predicted)) if len(np.unique(y))==2 else None,
        roc_auc=float(roc_auc_score(y,probability)) if len(np.unique(y))==2 else None,
        confusion_matrix=confusion_matrix(y,predicted,labels=[0,1]).tolist())


def block_ci(times, values, statistic=np.mean, *, seconds=30, repeats=1000, seed=20261108):
    """Resample contiguous clock blocks; include empty-in-cohort blocks.

    `times` must be the complete eligible time population. Values may contain NaN
    outside a quantile; those entries remain in blocks. Percentile pointwise CIs.
    """
    times=np.asarray(times,dtype=np.int64); values=np.asarray(values)
    labels=(times-times.min())//(seconds*1_000_000_000)
    groups=[np.flatnonzero(labels==k) for k in range(int(labels.max())+1)]
    if len(groups)<4:return None
    rng=np.random.default_rng(seed)
    estimates=[]
    for _ in range(repeats):
        idx=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
        sample=values[idx]
        if np.isfinite(sample).sum()<2:continue
        estimate=statistic(sample)
        if np.isfinite(estimate):estimates.append(float(estimate))
    return np.quantile(estimates,[.025,.975]).tolist() if estimates else None
