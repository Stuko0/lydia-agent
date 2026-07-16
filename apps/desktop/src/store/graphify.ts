import { Codecs, persistentAtom } from '@/lib/persisted'
import { PANE_TOGGLE_REVEAL_EVENT } from '@/components/pane-shell'

export const GRAPHIFY_PANE_ID = 'graphify'
const OPEN_KEY = 'lydia.desktop.graphifyOpen'

// Persisted so the pane stays open across reloads
export const $graphifyOpen = persistentAtom(OPEN_KEY, false, Codecs.bool)

export function toggleGraphify(): void {
  const current = $graphifyOpen.get()
  $graphifyOpen.set(!current)
  if (!current) {
    window.dispatchEvent(new CustomEvent(PANE_TOGGLE_REVEAL_EVENT, { detail: { id: GRAPHIFY_PANE_ID } }))
  }
}

export function closeGraphify(): void {
  $graphifyOpen.set(false)
}
