/** Session-scoped once-per-visit promo for the catalog pack (general platform only). */

export const CATALOG_PROMO_DISMISSED_KEY = 'aeo_catalog_promo_dismissed_v4'

/**
 * @param {{ getItem?: (key: string) => string | null }} storage
 * @returns {boolean}
 */
export function shouldShowCatalogPromo(storage) {
  try {
    if (!storage || typeof storage.getItem !== 'function') return true
    return storage.getItem(CATALOG_PROMO_DISMISSED_KEY) !== '1'
  } catch {
    return true
  }
}

/**
 * @param {{ setItem?: (key: string, value: string) => void }} storage
 */
export function dismissCatalogPromo(storage) {
  try {
    if (!storage || typeof storage.setItem !== 'function') return
    storage.setItem(CATALOG_PROMO_DISMISSED_KEY, '1')
  } catch {
    /* ignore quota / private mode */
  }
}
