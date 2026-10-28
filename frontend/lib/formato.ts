/** Número con coma decimal: 0.4567 → "0,46". */
export function coma(n: number, decimales = 2): string {
  return n.toFixed(decimales).replace(".", ",");
}

/** Variación con signo: 0.12 → "+0,12", -0.06 → "−0,06". */
export function conSigno(n: number): string {
  return (n >= 0 ? "+" : "−") + coma(Math.abs(n));
}
