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
    <section className="flex flex-col gap-3 rounded-[10px] border border-borde bg-white px-[18px] py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="m-0 text-base font-semibold">{titulo}</h2>
        {derecha}
      </div>
      {children}
    </section>
  );
}

export const clasesBoton =
  "min-h-11 cursor-pointer rounded-md px-4 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50";
export const clasesCampo =
  "min-h-11 rounded-md border border-borde-fuerte bg-white px-3 text-sm";
