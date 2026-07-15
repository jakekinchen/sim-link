import { api, mediaUrl, usePoll } from '../api/client'
import { EmptyState, ErrorState, Hash, KV, Panel, PassFail } from '../components/ui'
import { sci } from '../lib/format'

export default function Workcells() {
  const { data, error } = usePoll((signal) => api.workcells(signal), 15000)
  if (error && !data) return <ErrorState error={error} />
  const cells = data?.workcells ?? []
  if (cells.length === 0)
    return (
      <Panel title="workcells">
        <EmptyState>no built workcells — declare one via build_workcell_from_spec.py</EmptyState>
      </Panel>
    )
  return (
    <div className="flex flex-col gap-3">
      {cells.map((cell) => (
        <Panel
          key={cell.scene_id}
          title={`workcell · ${cell.scene_id}`}
          right={<PassFail value={cell.all_cubes_stable} />}
        >
          <p className="mb-3 font-mono text-2xs text-dim">“{cell.task_prompt}”</p>
          <div className="mb-3 grid grid-cols-2 gap-3">
            {Object.entries(cell.previews).map(([camera, path]) => (
              <figure key={camera}>
                <img src={mediaUrl(path)} alt={camera} className="w-full border border-line-2" />
                <figcaption className="cap mt-1">{camera}</figcaption>
              </figure>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-4">
            <KV label="cubes">{String(cell.cube_count ?? '—')}</KV>
            <KV label="trays">{String(cell.tray_count ?? '—')}</KV>
            <KV label="scene xml">
              <Hash value={cell.scene_xml_sha256} />
            </KV>
            <KV label="spec">
              <Hash value={cell.spec_sha256} />
            </KV>
            {Object.entries(cell.cube_stability ?? {}).map(([name, s]) => (
              <KV key={name} label={`${name} settle (m)`}>
                {sci(s.settle_displacement_m)} <PassFail value={s.stable} />
              </KV>
            ))}
          </div>
          <p className="cap mt-3 text-faint">{cell.authority}</p>
        </Panel>
      ))}
    </div>
  )
}
