import { CellOutput as CellOutputType } from '../stores/notebookStore'

interface Props {
  output: CellOutputType
}

export function CellOutput({ output }: Props) {
  switch (output.type) {
    case 'stream':
      return (
        <pre className={`text-sm whitespace-pre-wrap ${
          output.name === 'stderr' ? 'text-warning' : 'text-content-secondary'
        }`}>
          {output.text}
        </pre>
      )
    case 'execute_result':
      return (
        <div className="text-sm">
          {output.data?.['text/html'] ? (
            <div dangerouslySetInnerHTML={{ __html: output.data['text/html'] }} />
          ) : output.data?.['image/png'] ? (
            <img src={`data:image/png;base64,${output.data['image/png']}`} alt="Output" className="max-w-full rounded" />
          ) : output.data?.['image/svg+xml'] ? (
            <div dangerouslySetInnerHTML={{ __html: output.data['image/svg+xml'] }} />
          ) : (
            <pre className="text-content-secondary">{output.data?.['text/plain'] || ''}</pre>
          )}
        </div>
      )
    case 'display_data':
      return (
        <div className="text-sm">
          {output.data?.['image/png'] ? (
            <img src={`data:image/png;base64,${output.data['image/png']}`} alt="Display" className="max-w-full rounded" />
          ) : output.data?.['text/html'] ? (
            <div dangerouslySetInnerHTML={{ __html: output.data['text/html'] }} />
          ) : (
            <pre className="text-content-secondary">{output.data?.['text/plain'] || ''}</pre>
          )}
        </div>
      )
    case 'error':
      return (
        <div className="text-sm">
          <pre className="font-bold text-danger">{output.ename}: {output.evalue}</pre>
          {output.traceback && output.traceback.length > 0 && (
            <pre className="text-xs mt-1 text-danger/70">{output.traceback.join('\n')}</pre>
          )}
        </div>
      )
    default:
      return null
  }
}
