import { useState } from 'react'
import { useCCTVStore } from '@/store/cctvStore'
import type { CCTVStream } from '@/types'
import { Plus, Pencil, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'

interface FormState {
  name: string
  location: string
  stream_url: string
  enabled: boolean
}

const EMPTY_FORM: FormState = { name: '', location: '', stream_url: '', enabled: true }

export function CCTVManager() {
  const { streams, addStream, updateStream, removeStream, toggleStream } = useCCTVStore()
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [editing, setEditing] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const startEdit = (s: CCTVStream) => {
    setEditing(s.id)
    setForm({ name: s.name, location: s.location, stream_url: s.stream_url, enabled: s.enabled })
    setShowForm(true)
  }

  const cancel = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setShowForm(false)
  }

  const submit = async () => {
    if (!form.name || !form.stream_url) return
    if (editing) {
      await updateStream(editing, form)
    } else {
      await addStream(form)
    }
    cancel()
  }

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Kelola CCTV Stream</h3>
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-cv-online/20 text-cv-online border border-cv-online/30 rounded-lg hover:bg-cv-online/30 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Tambah
          </button>
        )}
      </div>

      {showForm && (
        <div className="border border-navy-700 rounded-lg p-3 space-y-2">
          <p className="text-xs text-slate-400 font-medium">{editing ? 'Edit Stream' : 'Tambah Stream Baru'}</p>
          {(['name', 'location', 'stream_url'] as const).map((field) => (
            <input
              key={field}
              placeholder={field === 'name' ? 'Nama' : field === 'location' ? 'Lokasi' : 'URL Stream (.m3u8)'}
              value={form[field]}
              onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
              className="w-full bg-navy-950 border border-navy-700 rounded px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cv-online/50"
            />
          ))}
          <div className="flex gap-2 pt-1">
            <button
              onClick={submit}
              className="text-xs px-3 py-1.5 bg-cv-online text-navy-950 rounded-lg font-medium hover:bg-cv-online/90 transition-colors"
            >
              Simpan
            </button>
            <button
              onClick={cancel}
              className="text-xs px-3 py-1.5 text-slate-400 hover:text-white transition-colors"
            >
              Batal
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {streams.map((s) => (
          <div
            key={s.id}
            className="flex items-center gap-3 p-2.5 rounded-lg bg-navy-950/50 border border-navy-800"
          >
            <div className={`w-2 h-2 rounded-full ${s.enabled ? 'bg-cv-online' : 'bg-cv-offline'}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">{s.name}</p>
              <p className="text-xs text-slate-500 truncate">{s.location}</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => toggleStream(s.id)}
                className="p-1.5 text-slate-400 hover:text-white transition-colors"
                title={s.enabled ? 'Nonaktifkan' : 'Aktifkan'}
              >
                {s.enabled ? (
                  <ToggleRight className="w-4 h-4 text-cv-online" />
                ) : (
                  <ToggleLeft className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={() => startEdit(s)}
                className="p-1.5 text-slate-400 hover:text-white transition-colors"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => removeStream(s.id)}
                className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
