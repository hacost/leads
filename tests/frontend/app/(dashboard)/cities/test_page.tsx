/**
 * SPRINT 4 — Frontend: cities-page test
 * Estrategia: Jest + React Testing Library + imports estáticos.
 */
import '@testing-library/jest-dom'
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'

// Mock de dependencias ANTES de importar el componente
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), put: jest.fn(), delete: jest.fn() },
}))
jest.mock('sonner', () => ({ toast: { error: jest.fn(), success: jest.fn() } }))

import api from '@/lib/api'
import MasterCitiesPage from '@/app/(dashboard)/cities/page'

beforeEach(() => jest.clearAllMocks())

// ---------------------------------------------------------------------------
// Test 4.1 — La página de ciudades renderiza state_name desde la API jerárquica
// ---------------------------------------------------------------------------
test('cities page renders state_name from hierarchical API response', async () => {
  const mockCities = [
    { id: 1, name: 'Monterrey', state_id: 1, state_name: 'NL', country_name: 'Mexico', status: 1, created_at: null },
  ]
  // api.get se llama tanto para /api/cities como para /api/countries (LocationCascader)
  ;(api.get as jest.Mock).mockResolvedValue(mockCities)

  render(<MasterCitiesPage />)

  // Esperamos que el state_name aparezca en la tabla
  await waitFor(() => {
    expect(screen.getByText('NL')).toBeInTheDocument()
  })
})
