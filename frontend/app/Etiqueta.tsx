// Uma etiqueta pequena, por exemplo o local ou o regime de uma vaga.
export default function Etiqueta({
  children,
  capitalizar = false,
}: {
  children: React.ReactNode;
  capitalizar?: boolean;
}) {
  return (
    <span
      className={`max-w-full truncate rounded-md border border-borda px-2 py-0.5 text-xs text-suave ${
        capitalizar ? "capitalize" : ""
      }`}
    >
      {children}
    </span>
  );
}
