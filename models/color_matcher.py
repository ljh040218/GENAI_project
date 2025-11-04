import numpy as np

def deltaE(lab1, lab2):
    a = np.array(lab1, dtype=np.float32)
    b = np.array(lab2, dtype=np.float32)
    return float(np.linalg.norm(a - b))
