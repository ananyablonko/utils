import sys; from pathlib import Path; d = Path(__file__).resolve().parent
sys.path.extend([str(d), str(d.parent)]); sys.path = list(set(sys.path))