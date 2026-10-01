/** Derive Odoo database name from shop URL hostname (no hardcoded gateway hosts). */
export function odooDatabaseDefault(shopUrl) {
  const raw = (shopUrl || '').trim()
  if (!raw) return ''
  try {
    const host = new URL(raw.includes('://') ? raw : `http://${raw}`).hostname.replace(/^www\./i, '')
    const label = host.split('.')[0]
    return label || ''
  } catch {
    return ''
  }
}

export function orderLineShopUrl(entitlement, connection) {
  const fromEntitlement = (entitlement?.aeo_connect_shop_url || '').trim()
  if (fromEntitlement) return fromEntitlement
  const fromStatus = (connection?.order_line_shop_url || '').trim()
  if (fromStatus) return fromStatus
  const nested = (connection?.order_line?.aeo_connect_shop_url || '').trim()
  return nested || ''
}
