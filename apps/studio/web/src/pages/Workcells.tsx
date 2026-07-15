import { lazy, Suspense, useState } from 'react'
import { api, ApiError, mediaUrl, usePoll } from '../api/client'
import type {
  WorkcellArrangementSpec,
  WorkcellColor,
  WorkcellCubeSpec,
  WorkcellManifest,
  WorkcellTraySpec,
} from '../api/types'
import { EmptyState, ErrorState, Hash, KV, Led, Panel, PassFail, Tag } from '../components/ui'
import { sci } from '../lib/format'

const COLORS: WorkcellColor[] = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
const WorkcellOrbit = lazy(() => import('../components/WorkcellOrbit'))

const DEFAULT_SPEC: WorkcellArrangementSpec = {
  schema_version: 'scenesmith.workcell_arrangement_spec.v1',
  scene_id: 'sorting_demo_two_cube',
  description: 'Studio draft based on the verified two-cube sorting example.',
  task_prompt:
    'Sort each cube into the same-colored tray: red cubes into the red tray and blue cubes into the blue tray.',
  trays: [
    { name: 'red_tray', color: 'red', center_m: [0.32, -0.12, 0.316] },
    { name: 'blue_tray', color: 'blue', center_m: [0.32, 0.12, 0.316] },
  ],
  cubes: [
    { name: 'red_cube', color: 'red', position_m: [0.2, -0.04, 0.325] },
    { name: 'blue_cube', color: 'blue', position_m: [0.2, 0.06, 0.325] },
  ],
}

function freshDefault(): WorkcellArrangementSpec {
  const draft = JSON.parse(JSON.stringify(DEFAULT_SPEC)) as WorkcellArrangementSpec
  const stamp = new Date().toISOString().replace(/\D/g, '').slice(0, 17)
  draft.scene_id = `studio_workcell_${stamp}`
  return draft
}

function serialize(spec: WorkcellArrangementSpec): string {
  return JSON.stringify(spec, null, 2)
}

function isVec3(value: unknown): value is [number, number, number] {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((coordinate) => typeof coordinate === 'number' && Number.isFinite(coordinate))
  )
}

function isFormSafeSpec(spec: WorkcellArrangementSpec): boolean {
  return (
    spec.schema_version === 'scenesmith.workcell_arrangement_spec.v1' &&
    typeof spec.scene_id === 'string' &&
    typeof spec.task_prompt === 'string' &&
    Array.isArray(spec.trays) &&
    spec.trays.every(
      (tray) =>
        tray !== null &&
        typeof tray === 'object' &&
        typeof tray.name === 'string' &&
        COLORS.includes(tray.color) &&
        isVec3(tray.center_m),
    ) &&
    Array.isArray(spec.cubes) &&
    spec.cubes.every(
      (cube) =>
        cube !== null &&
        typeof cube === 'object' &&
        typeof cube.name === 'string' &&
        COLORS.includes(cube.color) &&
        isVec3(cube.position_m),
    )
  )
}

function colorChip(color: WorkcellColor) {
  const swatches: Record<WorkcellColor, string> = {
    red: '#d94a4a',
    blue: '#3d73d9',
    green: '#4eb56f',
    yellow: '#d5b83e',
    purple: '#8a61cc',
    orange: '#dc7b35',
  }
  return (
    <span
      className="inline-block size-2 border border-white/15"
      style={{ backgroundColor: swatches[color] }}
      aria-hidden
    />
  )
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <label className="flex min-w-0 items-center gap-1">
      <span className="cap w-3 flex-none text-faint">{label}</span>
      <input
        className="field tabular min-w-0"
        type="number"
        step="0.001"
        value={value}
        onChange={(event) => {
          const next = Number(event.target.value)
          if (Number.isFinite(next)) onChange(next)
        }}
        aria-label={`${label} position in meters`}
      />
    </label>
  )
}

function PositionFields({
  value,
  onChange,
}: {
  value: [number, number, number]
  onChange: (value: [number, number, number]) => void
}) {
  return (
    <div className="grid grid-cols-3 gap-1">
      {(['x', 'y', 'z'] as const).map((axis, index) => (
        <NumberField
          key={axis}
          label={axis}
          value={value[index]}
          onChange={(next) => {
            const coordinates: [number, number, number] = [...value]
            coordinates[index] = next
            onChange(coordinates)
          }}
        />
      ))}
    </div>
  )
}

function ObjectRow({
  kind,
  item,
  onChange,
  onRemove,
}: {
  kind: 'cube' | 'tray'
  item: WorkcellCubeSpec | WorkcellTraySpec
  onChange: (item: WorkcellCubeSpec | WorkcellTraySpec) => void
  onRemove: () => void
}) {
  const position = 'position_m' in item ? item.position_m : item.center_m
  return (
    <div className="border border-line bg-inset p-2">
      <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_7.5rem_auto]">
        <label>
          <span className="cap mb-1 block">{kind} name</span>
          <input
            className="field"
            value={item.name}
            onChange={(event) => onChange({ ...item, name: event.target.value })}
          />
        </label>
        <label>
          <span className="cap mb-1 block">color</span>
          <span className="relative flex items-center">
            <span className="pointer-events-none absolute left-2 z-10 flex">
              {colorChip(item.color)}
            </span>
            <select
              className="field pl-6"
              value={item.color}
              onChange={(event) =>
                onChange({ ...item, color: event.target.value as WorkcellColor })
              }
            >
              {COLORS.map((color) => (
                <option key={color}>{color}</option>
              ))}
            </select>
          </span>
        </label>
        <button className="btn btn-quiet self-end" type="button" onClick={onRemove}>
          remove
        </button>
      </div>
      <div className="mt-2">
        <span className="cap mb-1 block">desk position · meters</span>
        <PositionFields
          value={position}
          onChange={(next) =>
            onChange(
              'position_m' in item
                ? { ...item, position_m: next }
                : { ...item, center_m: next },
            )
          }
        />
      </div>
    </div>
  )
}

function ManifestCard({ manifest, title }: { manifest: WorkcellManifest; title: string }) {
  return (
    <Panel
      title={title}
      right={<PassFail value={manifest.all_cubes_stable} />}
    >
      <p className="mb-3 font-mono text-2xs text-dim">“{manifest.task_prompt}”</p>
      {Object.keys(manifest.previews ?? {}).length > 0 && (
        <div className="mb-3 grid grid-cols-1 gap-3 md:grid-cols-2">
          {Object.entries(manifest.previews).map(([camera, path]) => (
            <figure key={camera}>
              <img src={mediaUrl(path)} alt={camera} className="w-full border border-line-2" />
              <figcaption className="cap mt-1">{camera}</figcaption>
            </figure>
          ))}
        </div>
      )}
      {manifest.scene_xml && <OrbitGate sceneXml={manifest.scene_xml} sceneId={manifest.scene_id} />}
      <div className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-4">
        <KV label="cubes">{String(manifest.cube_count ?? '—')}</KV>
        <KV label="trays">{String(manifest.tray_count ?? '—')}</KV>
        <KV label="scene xml">
          <Hash value={manifest.scene_xml_sha256} />
        </KV>
        <KV label="spec">
          <Hash value={manifest.spec_sha256} />
        </KV>
        {Object.entries(manifest.cube_stability ?? {}).map(([name, stability]) => (
          <KV key={name} label={`${name} settle (m)`}>
            {sci(stability.settle_displacement_m)} <PassFail value={stability.stable} />
          </KV>
        ))}
      </div>
      <p className="cap mt-3 text-faint">{manifest.authority}</p>
    </Panel>
  )
}

function OrbitGate({ sceneXml, sceneId }: { sceneXml: string; sceneId: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mb-3">
      <button
        type="button"
        className="flex w-full items-center gap-2 border border-line-2 bg-inset px-2 py-2 text-left hover:border-cyan/40"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span className={`text-faint transition-transform ${open ? 'rotate-90' : ''}`}>▸</span>
        <span className="cap text-cyan">3D orbit viewer</span>
        <span className="cap ml-auto text-faint">compiled scene.xml · local render</span>
      </button>
      {open && (
        <Suspense
          fallback={
            <div className="flex items-center gap-2 border border-line-2 border-t-0 p-3">
              <Led tone="amber" pulse />
              <span className="cap">loading Three.js viewport</span>
            </div>
          }
        >
          <WorkcellOrbit sceneXml={sceneXml} sceneId={sceneId} />
        </Suspense>
      )}
    </div>
  )
}

function Designer({ onBuilt }: { onBuilt: (manifest: WorkcellManifest) => void }) {
  const [initialSpec] = useState<WorkcellArrangementSpec>(() => freshDefault())
  const [spec, setSpec] = useState<WorkcellArrangementSpec>(initialSpec)
  const [jsonText, setJsonText] = useState(() => serialize(initialSpec))
  const [editorSynced, setEditorSynced] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [building, setBuilding] = useState(false)

  const commitSpec = (next: WorkcellArrangementSpec) => {
    setSpec(next)
    setJsonText(serialize(next))
    setEditorSynced(true)
    setError(null)
  }

  const parseEditor = (): WorkcellArrangementSpec | null => {
    try {
      const parsed = JSON.parse(jsonText) as unknown
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('Arrangement JSON must be an object.')
      }
      return parsed as WorkcellArrangementSpec
    } catch (parseError) {
      setError(parseError instanceof Error ? parseError.message : String(parseError))
      return null
    }
  }

  const applyEditor = () => {
    const parsed = parseEditor()
    if (!parsed) return
    if (!isFormSafeSpec(parsed)) {
      setError(
        'JSON parsed, but the form requires the v1 schema plus named, supported-color trays/cubes with finite XYZ coordinates. You can still build to run the full server validator.',
      )
      return
    }
    commitSpec(parsed)
  }

  const build = async () => {
    const parsed = parseEditor()
    if (!parsed) return
    setBuilding(true)
    setError(null)
    try {
      const manifest = await api.buildWorkcell(parsed)
      onBuilt(manifest)
    } catch (buildError) {
      if (buildError instanceof ApiError) {
        const detail = buildError.message.split(': ').slice(1).join(': ')
        const actionable = detail.trim().split('\n').at(-1)?.replace(/^ValueError:\s*/, '')
        setError(`${buildError.status} · ${actionable || detail}`)
      } else {
        setError(buildError instanceof Error ? buildError.message : String(buildError))
      }
    } finally {
      setBuilding(false)
    }
  }

  const updateCube = (index: number, next: WorkcellCubeSpec | WorkcellTraySpec) => {
    const cubes = [...spec.cubes]
    cubes[index] = next as WorkcellCubeSpec
    commitSpec({ ...spec, cubes })
  }

  const updateTray = (index: number, next: WorkcellCubeSpec | WorkcellTraySpec) => {
    const trays = [...spec.trays]
    trays[index] = next as WorkcellTraySpec
    commitSpec({ ...spec, trays })
  }

  return (
    <Panel
      title="arrangement intake · scenesmith.workcell_arrangement_spec.v1"
      right={
        <span className="flex items-center gap-2">
          <Tag tone="cyan">simulation fixture</Tag>
          <Led tone={building ? 'amber' : 'cyan'} pulse={building} />
        </span>
      }
      pad={false}
    >
      <div className="grid xl:grid-cols-[minmax(0,1.08fr)_minmax(28rem,0.92fr)]">
        <div className="space-y-4 border-b border-line p-3 xl:border-r xl:border-b-0">
          <div className="grid gap-3 md:grid-cols-2">
            <label>
              <span className="cap mb-1 block">scene id</span>
              <input
                className="field"
                value={spec.scene_id ?? ''}
                onChange={(event) => commitSpec({ ...spec, scene_id: event.target.value })}
                placeholder="sorting_demo_two_cube"
              />
            </label>
            <label>
              <span className="cap mb-1 block">description</span>
              <input
                className="field"
                value={spec.description ?? ''}
                onChange={(event) => commitSpec({ ...spec, description: event.target.value })}
                placeholder="Declared workcell purpose"
              />
            </label>
          </div>
          <label className="block">
            <span className="cap mb-1 block">task prompt</span>
            <textarea
              className="field min-h-16 resize-y"
              value={spec.task_prompt ?? ''}
              onChange={(event) => commitSpec({ ...spec, task_prompt: event.target.value })}
            />
          </label>

          <section>
            <div className="mb-2 flex items-center gap-2">
              <span className="cap text-ink">trays · {spec.trays?.length ?? 0}/4</span>
              <button
                className="btn btn-quiet ml-auto"
                type="button"
                disabled={(spec.trays?.length ?? 0) >= 4}
                onClick={() => {
                  const index = spec.trays.length
                  const color = COLORS[index % COLORS.length]
                  commitSpec({
                    ...spec,
                    trays: [
                      ...spec.trays,
                      {
                        name: `${color}_tray_${index + 1}`,
                        color,
                        center_m: [0.32, index % 2 === 0 ? -0.12 : 0.12, 0.316],
                      },
                    ],
                  })
                }}
              >
                + add tray
              </button>
            </div>
            <div className="space-y-2">
              {(spec.trays ?? []).map((tray, index) => (
                <ObjectRow
                  key={`tray-${index}`}
                  kind="tray"
                  item={tray}
                  onChange={(next) => updateTray(index, next)}
                  onRemove={() =>
                    commitSpec({ ...spec, trays: spec.trays.filter((_, item) => item !== index) })
                  }
                />
              ))}
            </div>
          </section>

          <section>
            <div className="mb-2 flex items-center gap-2">
              <span className="cap text-ink">cubes · {spec.cubes?.length ?? 0}/8</span>
              <button
                className="btn btn-quiet ml-auto"
                type="button"
                disabled={(spec.cubes?.length ?? 0) >= 8}
                onClick={() => {
                  const index = spec.cubes.length
                  const color = COLORS[index % COLORS.length]
                  commitSpec({
                    ...spec,
                    cubes: [
                      ...spec.cubes,
                      {
                        name: `${color}_cube_${index + 1}`,
                        color,
                        position_m: [0.2, -0.08 + index * 0.04, 0.325],
                      },
                    ],
                  })
                }}
              >
                + add cube
              </button>
            </div>
            <div className="space-y-2">
              {(spec.cubes ?? []).map((cube, index) => (
                <ObjectRow
                  key={`cube-${index}`}
                  kind="cube"
                  item={cube}
                  onChange={(next) => updateCube(index, next)}
                  onRemove={() =>
                    commitSpec({ ...spec, cubes: spec.cubes.filter((_, item) => item !== index) })
                  }
                />
              ))}
            </div>
          </section>
        </div>

        <div className="flex min-h-[34rem] flex-col bg-inset">
          <div className="flex items-center gap-2 border-b border-line px-3 py-2">
            <span className="cap text-ink">raw intake</span>
            <Tag tone={editorSynced ? 'green' : 'amber'}>
              {editorSynced ? 'form synced' : 'unapplied edit'}
            </Tag>
            <button className="btn btn-quiet ml-auto" type="button" onClick={applyEditor}>
              apply JSON
            </button>
          </div>
          <textarea
            className="min-h-[30rem] flex-1 resize-y bg-transparent p-3 font-mono text-2xs leading-relaxed text-cyan/90 outline-none focus:ring-1 focus:ring-inset focus:ring-cyan/50"
            value={jsonText}
            spellCheck={false}
            aria-label="Workcell arrangement JSON"
            onChange={(event) => {
              setJsonText(event.target.value)
              setEditorSynced(false)
              setError(null)
            }}
          />
          <div className="border-t border-line p-3">
            {error && (
              <div className="mb-3 border border-red/40 bg-red/8 p-2" role="alert">
                <div className="flex items-center gap-2">
                  <Led tone="red" />
                  <span className="cap text-red">intake rejected</span>
                </div>
                <p className="mt-1 whitespace-pre-wrap font-mono text-2xs text-red">{error}</p>
              </div>
            )}
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="btn btn-primary"
                type="button"
                disabled={building}
                onClick={() => void build()}
              >
                {building ? 'building + settling…' : 'build simulation fixture'}
              </button>
              <button
                className="btn btn-quiet"
                type="button"
                disabled={building}
                onClick={() => commitSpec(freshDefault())}
              >
                reset example
              </button>
              <span className="cap ml-auto text-faint">no training or promotion authority</span>
            </div>
          </div>
        </div>
      </div>
    </Panel>
  )
}

export default function Workcells() {
  const { data, error, refresh } = usePoll((signal) => api.workcells(signal), 15000)
  const [built, setBuilt] = useState<WorkcellManifest | null>(null)
  if (error && !data) return <ErrorState error={error} />
  const cells = data?.workcells ?? []
  const storedCells = built ? cells.filter((cell) => cell.scene_id !== built.scene_id) : cells
  return (
    <div className="flex flex-col gap-4">
      <Designer
        onBuilt={(manifest) => {
          setBuilt(manifest)
          refresh()
        }}
      />
      {built && <ManifestCard manifest={built} title={`new fixture · ${built.scene_id}`} />}
      <div className="flex items-center gap-2 pt-1">
        <span className="cap text-ink">compiled workcells</span>
        <Tag tone="dim">{cells.length}</Tag>
        {error && <span className="ml-auto font-mono text-2xs text-red">refresh fault</span>}
      </div>
      {storedCells.length === 0 && !built ? (
        <Panel>
          <EmptyState>no built workcells — use the arrangement intake above</EmptyState>
        </Panel>
      ) : (
        storedCells.map((cell) => (
          <ManifestCard key={cell.scene_id} manifest={cell} title={`workcell · ${cell.scene_id}`} />
        ))
      )}
    </div>
  )
}
