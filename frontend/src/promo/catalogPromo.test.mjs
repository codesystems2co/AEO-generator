import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import {
  CATALOG_PROMO_DISMISSED_KEY,
  dismissCatalogPromo,
  shouldShowCatalogPromo,
} from './catalogPromo.js'

function memoryStorage(seed = {}) {
  const map = new Map(Object.entries(seed))
  return {
    getItem(key) {
      return map.has(key) ? map.get(key) : null
    },
    setItem(key, value) {
      map.set(key, String(value))
    },
  }
}

describe('catalogPromo', () => {
  it('uses dismiss key v4 so updated copy shows again', () => {
    assert.equal(CATALOG_PROMO_DISMISSED_KEY, 'aeo_catalog_promo_dismissed_v4')
  })

  it('shows on first visit (empty storage)', () => {
    assert.equal(shouldShowCatalogPromo(memoryStorage()), true)
  })

  it('does not show after dismiss', () => {
    const storage = memoryStorage()
    dismissCatalogPromo(storage)
    assert.equal(storage.getItem(CATALOG_PROMO_DISMISSED_KEY), '1')
    assert.equal(shouldShowCatalogPromo(storage), false)
  })

  it('does not show again after record-on-show (reload rule)', () => {
    const storage = memoryStorage()
    assert.equal(shouldShowCatalogPromo(storage), true)
    dismissCatalogPromo(storage)
    assert.equal(shouldShowCatalogPromo(storage), false)
  })

  it('shows again with a fresh storage', () => {
    const first = memoryStorage()
    dismissCatalogPromo(first)
    assert.equal(shouldShowCatalogPromo(first), false)
    assert.equal(shouldShowCatalogPromo(memoryStorage()), true)
  })
})
