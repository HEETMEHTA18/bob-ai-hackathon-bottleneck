import { useCallback, useState } from 'react'
import { uploadCSV } from '../../api/client'
import { useSiteContext } from '../../context/SiteContext'
import { Button } from '../common/LoadingSkeleton'

export function CSVUpload() {
  const { activeSite } = useSiteContext()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleFile = useCallback(async (file: File) => {
    if (!activeSite) return
    setUploading(true)
    try {
      const res = await uploadCSV(activeSite.id, file)
      setResult(res.data)
    } catch (e: any) {
      setResult({ error: e.message })
    } finally {
      setUploading(false)
    }
  }, [activeSite])

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-all ${dragging ? 'scale-[1.01]' : ''}`}
      style={{ borderColor: dragging ? 'var(--accent)' : 'var(--border)', background: dragging ? 'var(--accent-light)' : 'var(--bg-secondary)' }}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
    >
      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
          <p className="text-sm font-medium" style={{ color: 'var(--accent)' }}>Uploading...</p>
        </div>
      ) : result ? (
        <div className="animate-fadeIn">
          {result.error ? (
            <div>
              <div className="w-10 h-10 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: 'var(--red-light)' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              </div>
              <p className="text-sm" style={{ color: 'var(--red)' }}>{result.error}</p>
            </div>
          ) : (
            <div>
              <div className="w-10 h-10 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: 'var(--green-light)' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <p className="text-sm font-semibold" style={{ color: 'var(--green)' }}>Upload successful!</p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{result.rows} rows processed</p>
            </div>
          )}
          <button onClick={() => setResult(null)} className="mt-3 text-xs font-medium" style={{ color: 'var(--accent)' }}>Upload another</button>
        </div>
      ) : (
        <div>
          <div className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center" style={{ background: 'var(--bg-tertiary)' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </div>
          <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Drop your CSV file here</p>
          <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Requires 'timestamp' and 'generation_kw' columns</p>
          <label className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer text-sm font-medium transition-colors hover:bg-gray-50" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
            Browse Files
            <input type="file" accept=".csv" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
          </label>
        </div>
      )}
    </div>
  )
}
