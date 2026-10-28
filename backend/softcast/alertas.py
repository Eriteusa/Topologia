# Motor de alertas tempranas (CONTEXTO §8).
NORMAL = "Normal"
ALERTA = "Alerta temprana"
ANOMALO = "Anómalo"
BLOQUEADO = "Bloqueado"

P_ALERTA = 0.40
P_ANOMALO = 0.50


def nivel(p_anomalo, secuencia_valida, bloqueado=False):
    """
    p_anomalo: probabilidad de clase Anómalo que da la GNN.
    Los nodos bloqueados no tienen nivel de alerta: su nivel es "Bloqueado".
    """
    if bloqueado:
        return BLOQUEADO
    if p_anomalo >= P_ANOMALO:
        return ANOMALO
    if p_anomalo >= P_ALERTA or not secuencia_valida:
        return ALERTA
    return NORMAL
