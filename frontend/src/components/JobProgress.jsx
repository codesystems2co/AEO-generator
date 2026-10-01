import { useEffect, useRef, useState } from 'react'
import './JobProgress.css'

const ICONS = {
  plug: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M9 7V3h2v4h2V3h2v4h1a2 2 0 0 1 2 2v4.5a6.5 6.5 0 0 1-5 6.32V22h-2v-2.18A6.5 6.5 0 0 1 8 13.5V9a2 2 0 0 1 2-2h-1Z" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M10.5 4a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13Zm0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Zm7.2 10.1 3.1 3.1-1.4 1.4-3.1-3.1 1.4-1.4Z" />
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M5 4h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-4 3v-3H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm2 5v2h10V9H7Zm0 4v2h7v-2H7Z" />
    </svg>
  ),
  tag: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M3 12.5 12.5 3H20v7.5L10.5 21 3 13.5v-1ZM16.5 8A1.5 1.5 0 1 0 16.5 5a1.5 1.5 0 0 0 0 3Z" />
    </svg>
  ),
  upload: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M11 16V7.8l-3.1 3.1-1.4-1.4L12 4l5.5 5.5-1.4 1.4L13 7.8V16h-2Zm-7 4v-2h16v2H4Z" />
    </svg>
  ),
  file: (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d="M6 2h8l6 6v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm7 1.5V9h5.5L13 3.5ZM8 12h8v2H8v-2Zm0 4h8v2H8v-2Z" />
    </svg>
  ),
}

export default function JobProgress({
  progress,
  message,
  onDownload,
  downloading,
  canDownload,
  kicker,
  hint,
  downloadLabel,
  downloadingLabel,
  tasksKicker,
  tasksTitle,
  focusDownload,
}) {
  const percent = progress?.percent || 0
  const items = progress?.items || []
  const done = items.filter((item) => item.done).length
  const [openTasks, setOpenTasks] = useState(false)
  const downloadRef = useRef(null)
  useEffect(() => {
    if (!canDownload || !focusDownload) return
    downloadRef.current?.focus()
  }, [canDownload, focusDownload])
  return (
    <section className="job-progress" aria-label={kicker || 'Progress'}>
      <div className="job-progress-head">
        <div>
          <p className="job-progress-kicker">{kicker || 'Asistente en curso'}</p>
          <p className="job-progress-copy">{message}</p>
        </div>
        <strong className="job-progress-pct" aria-live="polite">{percent}%</strong>
      </div>
      <div
        className={`job-progress-track ${progress?.loading ? 'is-loading' : ''}`}
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <span className="job-progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="job-progress-tasks">
        <button
          type="button"
          className="job-progress-tasks-trigger"
          aria-expanded={openTasks}
          aria-controls="job-progress-tasks"
          onClick={() => setOpenTasks((value) => !value)}
        >
          <span className="job-progress-tasks-copy">
            <span className="job-progress-kicker">{tasksKicker || 'Tareas'}</span>
            <span className="job-progress-tasks-title">{tasksTitle || 'Por completar'}</span>
          </span>
          <span className="job-progress-tasks-meta">
            <span className="job-progress-tasks-count">{done} / {items.length}</span>
            <svg className={`job-progress-chevron${openTasks ? ' is-open' : ''}`} viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M7.4 9.2 12 13.8l4.6-4.6 1.4 1.4L12 16.6 6 11.6l1.4-1.4Z" />
            </svg>
          </span>
        </button>
        {openTasks ? (
          <ol id="job-progress-tasks" className="job-progress-steps">
            {items.map((item) => (
              <li
                key={item.id}
                className={[
                  item.done ? 'done' : '',
                  progress?.current?.id === item.id && !item.done ? 'current' : '',
                ].join(' ').trim()}
              >
                <span className="job-progress-icon">{ICONS[item.icon] || ICONS.file}</span>
                <span className="job-progress-label">{item.label}</span>
                <span className="job-progress-detail">{item.detail}</span>
              </li>
            ))}
          </ol>
        ) : null}
      </div>
      {canDownload ? (
        <div className="job-progress-actions">
          <button
            ref={downloadRef}
            type="button"
            className="btn btn-download"
            disabled={downloading}
            onClick={onDownload}
          >
            <svg className="btn-download-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="currentColor" d="M6 2h8l6 6v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm7 1.5V9h5.5L13 3.5ZM8 13h3v4h2v-4h3l-4-4-4 4Z" />
            </svg>
            {downloading ? (downloadingLabel || 'Preparing…') : (downloadLabel || 'Descargar Informe')}
          </button>
        </div>
      ) : (
        <p className="job-progress-hint">
          {hint}
        </p>
      )}
    </section>
  )
}
