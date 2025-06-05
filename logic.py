from typing import Iterable, Optional

def most(iterable: Iterable, *,
        n_fail: Optional[int] = 1,
        p_fail: Optional[float] = 0.2
    ) -> bool:
    check = [bool(x) for x in iterable]
    n_passed = sum(check)
    n_total = len(check)
    passed = n_passed == n_total
    if passed:
        return passed

    if n_fail is not None:
        passed |= n_total - n_passed <= n_fail
    if p_fail is not None:
        passed |= n_total > 0 and (n_total - n_passed) / n_total < p_fail
    
    return passed