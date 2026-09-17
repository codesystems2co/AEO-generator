import './TreeList.css'

export default function TreeList({ nodes, rootLabel }) {
  if (!nodes?.length) return null
  return (
    <div className="tree-wrap">
      {rootLabel && <div className="tree-root">{rootLabel}</div>}
      <ul className="tree">
        {nodes.map((node, i) => (
          <TreeNode key={`${node.label}-${i}`} node={node} />
        ))}
      </ul>
    </div>
  )
}

function TreeNode({ node }) {
  const kids = node.children || []
  return (
    <li>
      <div className="tree-row">
        <span className="tree-label">{node.label}</span>
        {node.value ? <span className="tree-value">{node.value}</span> : null}
      </div>
      {kids.length > 0 && (
        <ul className="tree">
          {kids.map((child, i) => (
            <TreeNode key={`${child.label}-${i}`} node={child} />
          ))}
        </ul>
      )}
    </li>
  )
}
