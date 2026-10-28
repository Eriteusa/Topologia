# Efecto de simular fallas (semilla 42, sin bloqueos)

| Nodo | Tráfico | CPU | Estado antes → después | p anómalo antes → después | Otros nodos que cambiaron |
| --- | --- | --- | --- | --- | --- |
| PC1 | 35 → 35 | 42 → 95 | Normal → Anómalo | 0,17 → 0,90 | S1 (+0,06), S2 (+0,25), PC2 (+0,38), PC3 (+0,06), IoT1 (+0,12) |
| IoT3 | 20 → 90 | 25 → 25 | Normal → Anómalo | 0,00 → 0,63 | S1 (+0,12), S2 (+0,03) |
| S2 | 71 → 90 | 68 → 95 | Normal → Anómalo | 0,33 → 0,76 | S1 (+0,35), PC1 (+0,11), PC2 (+0,18), PC3 (+0,19), PC4 (+0,12), PC5 (+0,02), PC6 (+0,03), IoT1 (+0,03), IoT6 (+0,02) |
| PC4 | 65 → 20 | 72 → 25 | Normal → Normal | 0,10 → 0,00 | S1 (−0,10), S2 (−0,15), PC1 (−0,02), PC2 (−0,05), PC3 (−0,13) |
