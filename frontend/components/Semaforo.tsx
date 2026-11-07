export type LuzSemaforo = "rojo" | "ambar" | "verde";

const LUCES: { luz: LuzSemaforo; color: string; nombre: string }[] = [
  { luz: "rojo", color: "#e5483d", nombre: "Anómalo" },
  { luz: "ambar", color: "#f5b301", nombre: "Alerta temprana" },
  { luz: "verde", color: "#2fb463", nombre: "Normal" },
];

/** Logo en forma de semáforo; la luz encendida resume el estado de la red. */
export default function Semaforo({ activa }: { activa: LuzSemaforo }) {
  const nombre = LUCES.find((l) => l.luz === activa)?.nombre;
  return (
    <svg width="26" height="40" viewBox="0 0 26 40" role="img" aria-label={`Estado de la red: ${nombre}`}>
      <rect x="1" y="1" width="24" height="38" rx="9" fill="#2b2f36" />
      {LUCES.map(({ luz, color }, i) => {
        const encendida = luz === activa;
        return (
          <circle
            key={luz}
            cx="13"
            cy={9.5 + i * 10.5}
            r="4"
            fill={color}
            opacity={encendida ? 1 : 0.22}
            className={encendida ? "animate-brillo" : "transition-opacity duration-300"}
            style={{ color }}
          />
        );
      })}
    </svg>
  );
}
