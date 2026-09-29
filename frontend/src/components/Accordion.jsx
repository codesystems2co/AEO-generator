import './Accordion.css'

function Chevron({ open }) {
  return (
    <svg className={`accordion-chevron ${open ? 'is-open' : ''}`} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M7.4 9.2 12 13.8l4.6-4.6 1.4 1.4L12 16.6 6 11.6l1.4-1.4Z"
      />
    </svg>
  )
}

export default function Accordion({ children }) {
  return <div className="accordion">{children}</div>
}

export function AccordionPanel({
  id,
  kicker,
  title,
  summary,
  open,
  onToggle,
  children,
}) {
  return (
    <section className={`accordion-panel ${open ? 'is-open' : ''}`}>
      <h3 className="accordion-heading">
        <button
          type="button"
          className="accordion-trigger"
          aria-expanded={open}
          aria-controls={id}
          onClick={onToggle}
        >
          <span className="accordion-copy">
            {kicker ? <span className="accordion-kicker">{kicker}</span> : null}
            <span className="accordion-title">{title}</span>
            {summary ? <span className="accordion-summary">{summary}</span> : null}
          </span>
          <Chevron open={open} />
        </button>
      </h3>
      {open ? (
        <div id={id} className="accordion-body">
          {children}
        </div>
      ) : null}
    </section>
  )
}
