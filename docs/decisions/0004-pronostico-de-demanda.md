# ADR 0004: Pronóstico semanal de demanda

## Contexto

`smartstore analyze` ya resume ítems por semana. El inventario necesita una cifra
para las semanas que todavía no ocurrieron, y el método tiene que poder explicarse
sin un modelo opaco.

## Decisión

- **Unidad:** ítems por semana ISO. Una fila con `is_valid_sale = true` es un ítem.
- **Huecos:** las semanas sin ventas, entre la primera y la última, valen 0.
- **Tres reglas**, cada una usa solo el pasado:
  - último valor;
  - promedio de las últimas 4 semanas;
  - el valor de hace 52 semanas.
- **Elección:** menor MAE en las últimas semanas (como máximo la mitad de la serie
  y nunca más que el horizonte). Si empatan, gana la regla más simple.
- El pronóstico que se publica sí usa toda la historia, incluidas esas semanas.

## Consecuencias

- Con menos de un año de historia, la regla estacional se comporta como el último valor.
- `smartstore forecast` escribe la serie, el pronóstico y un gráfico en
  `data/processed/` y `docs/reports/`.
- Un modelo más elaborado solo se justifica si baja este error.

## Estado

Aceptado — 2026-11-05
