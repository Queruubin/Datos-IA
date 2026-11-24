export interface QuickStart {
  title: string
  question: string
}

/** Quick-start cards shown in the empty chat and in the last welcome step. */
export const QUICK_STARTS: QuickStart[] = [
  { title: 'Inversión por sector', question: 'Muéstrame la inversión 2026 por sector' },
  { title: 'Quejas más frecuentes', question: '¿De qué se queja más la gente?' },
  { title: 'Ejecución del presupuesto', question: '¿Cuánto se ejecutó del presupuesto en 2025?' },
  { title: 'Presupuestos participativos', question: '¿Las propuestas priorizadas tienen contratos?' },
  { title: 'Plan vs seguimiento', question: '¿Coincide lo planeado en el POAI con el seguimiento de metas?' },
  { title: 'Inversión por ODS', question: '¿Cuánto se planeó invertir en 2026 por Objetivo de Desarrollo Sostenible?' },
]

export const EXAMPLE_QUESTIONS = QUICK_STARTS.map((item) => item.question)
