import type { ReactNode } from "react";

export default function Panel({
  titulo,
  derecha,
  children,
}: {
  titulo: string;
  derecha?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="flex animate-entrar flex-col gap-3 rounded-2xl border border-borde bg-white px-5 py-4 shadow-[0_1px_2px_rgba(16,24,40,0.05)]">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="m-0 text-[15px] font-semibold">{titulo}</h2>
        {derecha}
      </div>
      {children}
    </section>
  );
}

export const clasesBoton =
  "min-h-11 cursor-pointer rounded-xl px-4 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50";
export const clasesCampo =
  "min-h-11 rounded-xl border border-borde-fuerte bg-white px-3 text-sm outline-none transition-colors focus:border-[#2b2f36]";
/** Botón principal: gris oscuro. */
export const botonPrimario = "bg-[#2b2f36] text-white hover:bg-[#1a1d22]";
/** Botón secundario: blanco con borde. */
export const botonSecundario = "border border-borde-fuerte bg-white text-tinta hover:bg-fondo";
