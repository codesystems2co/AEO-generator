import './TreeList.css'

function displayLabel(label) {
  const text = String(label ?? '')
  const match = text.match(/['"]text['"]\s*:\s*(['"])([\s\S]*?)\1/)
  const value = match ? match[2] : text
  if (/Page title:|Internal graph:|Hostname:/.test(value)) {
    return 'La tienda responde, pero la página todavía no tiene título, encabezado ni descripción. No hay datos estructurados.'
  }
  return value
}

export default function TreeList({ nodes, rootLabel, solving = false, activeLabel = '' }) {
  if (!nodes?.length) return null
  return (
    <div className="tree-wrap">
      {rootLabel && <div className={`tree-root${solving ? ' is-solving' : ''}`}>{rootLabel}</div>}
      <ul className="tree">
        {nodes.map((node, i) => (
          <TreeNode key={`${node.label}-${i}`} node={node} activeLabel={activeLabel} />
        ))}
      </ul>
    </div>
  )
}

function TreeNode({ node, activeLabel }) {
  const kids = node.children || []
  const solving = Boolean(activeLabel) && node.label === activeLabel
  return (
    <li>
      <div className="tree-row">
        <span className={`tree-label${solving ? ' is-solving' : ''}`}>{displayLabel(node.label)}</span>
        {node.value ? <span className="tree-value">{displayLabel(node.value)}</span> : null}
      </div>
      {kids.length > 0 && (
        <ul className="tree">
          {kids.map((child, i) => (
            <TreeNode key={`${child.label}-${i}`} node={child} activeLabel={solving ? '' : activeLabel} />
          ))}
        </ul>
      )}
    </li>
  )
}
