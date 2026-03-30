/**
 * SPRINT 4 — Frontend: create-job-page test
 * Estrategia: Jest + React Testing Library + imports estáticos + fireEvent.
 */
import '@testing-library/jest-dom'
import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

// Mocks ANTES de importar el componente
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}))
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
}))
jest.mock('sonner', () => ({ toast: { error: jest.fn(), success: jest.fn() } }))

import api from '@/lib/api'
import CreateBatchPage from '@/app/(dashboard)/batch/create/page'

beforeEach(() => jest.clearAllMocks())

// ---------------------------------------------------------------------------
// Test 4.2 — Al montar, el componente hace fetch de /api/countries (vía LocationCascader)
// ---------------------------------------------------------------------------
test('create-job page fetches /api/countries on mount', async () => {
  ;(api.get as jest.Mock).mockResolvedValue([{ id: 1, name: 'Mexico' }])

  render(<CreateBatchPage />)

  await waitFor(() => {
    expect(api.get).toHaveBeenCalledWith('/api/countries')
  })
})

// ---------------------------------------------------------------------------
// Test 4.3 — Seleccionar un país activa el fetch de /api/states?country_id=1
// ---------------------------------------------------------------------------
test('selecting a country triggers fetch of /api/states?country_id=1', async () => {
  ;(api.get as jest.Mock)
    .mockResolvedValueOnce([{ id: 1, name: 'Mexico' }])             // countries
    .mockResolvedValueOnce([{ id: 1, name: 'Categorias' }])         // categories
    .mockResolvedValueOnce([{ id: 1, name: 'NL', country_id: 1 }])  // states

  render(<CreateBatchPage />)

  // Esperar que el select de país esté habilitado (countries data loaded)
  const countrySelect = await screen.findByRole('combobox', { name: /country/i })
  await waitFor(() => expect(countrySelect).not.toBeDisabled())
  fireEvent.change(countrySelect, { target: { value: '1' } })

  await waitFor(() => {
    expect(api.get).toHaveBeenCalledWith('/api/states?country_id=1')
  })
})

// ---------------------------------------------------------------------------
// Test 4.4 — Seleccionar un estado activa el fetch de /api/cities?state_id=1
// ---------------------------------------------------------------------------
test('selecting a state triggers fetch of /api/cities?state_id=1', async () => {
  ;(api.get as jest.Mock)
    .mockResolvedValueOnce([{ id: 1, name: 'Mexico' }])                // countries
    .mockResolvedValueOnce([{ id: 1, name: 'Categorias' }])            // categories
    .mockResolvedValueOnce([{ id: 1, name: 'NL', country_id: 1 }])     // states
    .mockResolvedValueOnce([{ id: 1, name: 'Monterrey', state_id: 1 }]) // cities

  render(<CreateBatchPage />)

  // Seleccionar país — esperar que esté habilitado y hacer change
  const countrySelect = await screen.findByRole('combobox', { name: /country/i })
  await waitFor(() => expect(countrySelect).not.toBeDisabled())
  fireEvent.change(countrySelect, { target: { value: '1' } })

  // Seleccionar estado — esperar que se habilite tras fetch de states
  const stateSelect = await screen.findByRole('combobox', { name: /state/i })
  await waitFor(() => expect(stateSelect).not.toBeDisabled())
  fireEvent.change(stateSelect, { target: { value: '1' } })

  await waitFor(() => {
    expect(api.get).toHaveBeenCalledWith('/api/cities?state_id=1')
  })
})
