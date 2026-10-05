import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { deriveStoreProfile } from './storeProfile.js'

const FERRUM_PAGE = {
  title: 'Ferrum Aditiva | Impresión 3D en metal DMLS/SLM',
  meta_description:
    'Fabricación aditiva en metal DMLS/SLM para piezas industriales de alta precisión.',
  h1_list: ['Impresión 3D en metal DMLS/SLM'],
  og_site_name: 'Ferrum Aditiva',
  organization_name: 'Ferrum Aditiva',
}

describe('deriveStoreProfile', () => {
  it('Ferrum-style page → business Ferrum Aditiva, topic from H1, facts from meta', () => {
    const profile = deriveStoreProfile(FERRUM_PAGE, {}, 'Gap advertisements tool highs')
    assert.equal(profile.business, 'Ferrum Aditiva')
    assert.equal(profile.topic, 'Impresión 3D en metal DMLS/SLM')
    assert.equal(
      profile.facts,
      'Fabricación aditiva en metal DMLS/SLM para piezas industriales de alta precisión.',
    )
  })

  it('uses title brand and topic when H1/org/og missing', () => {
    const profile = deriveStoreProfile(
      {
        title: 'Ferrum Aditiva | Impresión 3D en metal DMLS/SLM',
        meta_description: 'Metal 3D printing for industry.',
        h1_list: [],
      },
      {},
      'Gap advertisements tool highs',
    )
    assert.equal(profile.business, 'Ferrum Aditiva')
    assert.equal(profile.topic, 'Impresión 3D en metal DMLS/SLM')
    assert.match(profile.facts, /Metal 3D printing/)
  })

  it('prefers remediation when present', () => {
    const profile = deriveStoreProfile(
      FERRUM_PAGE,
      {
        title: 'Other Brand | Other Topic',
        meta_description: 'Remediation meta about the offer.',
        h1: 'Remediation H1 topic',
        organization_name: 'Remediation Org',
      },
      'Host Stem',
    )
    assert.equal(profile.business, 'Remediation Org')
    assert.equal(profile.topic, 'Remediation H1 topic')
    assert.equal(profile.facts, 'Remediation meta about the offer.')
  })

  it('falls back to hostname stem only as last resort', () => {
    const profile = deriveStoreProfile({}, {}, 'Gap advertisements tool highs')
    assert.equal(profile.business, 'Gap advertisements tool highs')
    assert.equal(profile.topic, 'Gap advertisements tool highs')
    assert.equal(profile.facts, '')
  })

  it('appends H1 to facts when not redundant with meta', () => {
    const profile = deriveStoreProfile({
      title: 'Brand | Topic',
      meta_description: 'We sell industrial parts.',
      h1_list: ['Impresión 3D en metal'],
      organization_name: 'Brand',
    })
    assert.equal(profile.facts, 'We sell industrial parts.\nImpresión 3D en metal')
  })
})
