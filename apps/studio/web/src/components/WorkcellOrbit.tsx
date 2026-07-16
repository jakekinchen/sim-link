import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { mediaUrl } from '../api/client'
import { Led, Tag } from './ui'

interface SceneSummary {
  boxes: number
  cubes: number
  trays: number
  flows: TaskFlowSummary[]
}

interface TaskFlowSummary {
  id: string
  label: string
  color: string
}

interface AnimatedFlow {
  id: string
  curve: THREE.CatmullRomCurve3
  group: THREE.Group
  packet: THREE.Mesh
  sourceRing: THREE.Mesh
  targetRing: THREE.Mesh
  phase: number
}

type CameraPreset = 'perspective' | 'overhead' | 'side'

const TASK_COLORS: Record<string, number> = {
  red: 0xff4f57,
  blue: 0x2d8cff,
  green: 0x4be39d,
  yellow: 0xffd35c,
  purple: 0xa896ff,
  orange: 0xff9a4d,
}

function taskColor(name: string): { name: string; hex: number } | null {
  const normalized = name.toLowerCase()
  const match = Object.entries(TASK_COLORS).find(([color]) => normalized.includes(color))
  return match ? { name: match[0], hex: match[1] } : null
}

function numbers(value: string | null, fallback: number[]): number[] {
  if (!value) return fallback
  const parsed = value
    .trim()
    .split(/\s+/)
    .map(Number)
  if (parsed.length === 0 || !parsed.every(Number.isFinite)) {
    throw new Error(`Compiled workcell XML contains a non-finite numeric field: ${value}`)
  }
  return parsed
}

function applyTransform(object: THREE.Object3D, element: Element) {
  const position = numbers(element.getAttribute('pos'), [0, 0, 0])
  if (position.length !== 3) throw new Error('Compiled workcell XML contains a malformed position.')
  object.position.set(position[0], position[1], position[2])
  const quaternion = numbers(element.getAttribute('quat'), [1, 0, 0, 0])
  if (quaternion.length !== 4) throw new Error('Compiled workcell XML contains a malformed quaternion.')
  const rotation = new THREE.Quaternion(quaternion[1], quaternion[2], quaternion[3], quaternion[0])
  if (rotation.lengthSq() < 1e-12) throw new Error('Compiled workcell XML contains a zero quaternion.')
  object.quaternion.copy(rotation.normalize())
}

function addGeom(element: Element, parent: THREE.Group): boolean {
  const name = element.getAttribute('name') ?? 'unnamed_geom'
  if (/wall|ceiling/.test(name)) return false
  const type = element.getAttribute('type') ?? 'sphere'
  const size = numbers(element.getAttribute('size'), [])
  let geometry: THREE.BufferGeometry | null = null
  if (type === 'box' && size.length >= 3) {
    if (size.slice(0, 3).some((value) => value <= 0)) {
      throw new Error(`Compiled workcell box ${name} has a non-positive size.`)
    }
    geometry = new THREE.BoxGeometry(size[0] * 2, size[1] * 2, size[2] * 2)
  } else if (type === 'plane' && size.length >= 2) {
    if (size.slice(0, 2).some((value) => value <= 0)) {
      throw new Error(`Compiled workcell plane ${name} has a non-positive size.`)
    }
    geometry = new THREE.BoxGeometry(size[0] * 2, size[1] * 2, 0.008)
  }
  if (!geometry) return false

  const rgba = numbers(element.getAttribute('rgba'), [0.48, 0.54, 0.62, 1])
  if (rgba.length !== 3 && rgba.length !== 4) {
    throw new Error(`Compiled workcell geom ${name} has malformed RGBA.`)
  }
  if (rgba.slice(0, 4).some((value) => value < 0 || value > 1)) {
    throw new Error(`Compiled workcell geom ${name} has RGBA outside [0, 1].`)
  }
  const alpha = Math.max(0.08, Math.min(1, rgba[3] ?? 1))
  const color = new THREE.Color(rgba[0] ?? 0.48, rgba[1] ?? 0.54, rgba[2] ?? 0.62)
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.72,
    metalness: 0.04,
    transparent: alpha < 1,
    opacity: alpha,
    side: THREE.DoubleSide,
  })
  const mesh = new THREE.Mesh(geometry, material)
  mesh.name = name
  applyTransform(mesh, element)
  mesh.castShadow = !/wall|ceiling|floor/.test(mesh.name)
  mesh.receiveShadow = true

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry),
    new THREE.LineBasicMaterial({
      color: color.clone().multiplyScalar(1.3),
      transparent: true,
      opacity: Math.min(0.78, alpha + 0.2),
    }),
  )
  mesh.add(edges)
  parent.add(mesh)
  return true
}

function addRobotPlaceholder(root: THREE.Group) {
  const material = new THREE.MeshStandardMaterial({
    color: 0xf2c230,
    roughness: 0.55,
    metalness: 0.18,
  })
  const dark = new THREE.MeshStandardMaterial({
    color: 0x252b34,
    roughness: 0.68,
    metalness: 0.24,
  })
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.052, 0.045, 24), material)
  base.rotation.x = Math.PI / 2
  base.position.set(-0.06, 0, 0.335)
  base.castShadow = true
  root.add(base)

  const points = [
    new THREE.Vector3(-0.06, 0, 0.37),
    new THREE.Vector3(-0.03, 0, 0.45),
    new THREE.Vector3(0.055, 0, 0.52),
    new THREE.Vector3(0.145, 0, 0.47),
    new THREE.Vector3(0.205, 0, 0.405),
  ]
  for (let index = 0; index < points.length - 1; index += 1) {
    const start = points[index]
    const end = points[index + 1]
    const direction = end.clone().sub(start)
    const link = new THREE.Mesh(
      new THREE.CylinderGeometry(0.018, 0.018, direction.length(), 16),
      index % 2 === 0 ? material : dark,
    )
    link.position.copy(start).add(end).multiplyScalar(0.5)
    link.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize())
    link.castShadow = true
    root.add(link)
    const joint = new THREE.Mesh(new THREE.SphereGeometry(0.025, 18, 12), dark)
    joint.position.copy(end)
    joint.castShadow = true
    root.add(joint)
  }
  const gripper = new THREE.Mesh(new THREE.BoxGeometry(0.065, 0.055, 0.022), material)
  gripper.position.copy(points.at(-1) as THREE.Vector3)
  gripper.rotation.z = -0.35
  gripper.castShadow = true
  root.add(gripper)
}

function buildSceneGeometry(
  xmlText: string,
  root: THREE.Group,
  animatedFlows: AnimatedFlow[],
): SceneSummary {
  const document = new DOMParser().parseFromString(xmlText, 'application/xml')
  if (document.querySelector('parsererror')) throw new Error('Compiled workcell XML could not be parsed.')
  const worldbody = document.querySelector('worldbody')
  if (!worldbody) throw new Error('Compiled workcell XML has no worldbody.')

  const cubes = new Set<string>()
  const trays = new Set<string>()
  let boxes = 0

  const visit = (element: Element, parent: THREE.Group) => {
    for (const child of Array.from(element.children)) {
      if (child.tagName === 'body') {
        const group = new THREE.Group()
        group.name = child.getAttribute('name') ?? 'unnamed_body'
        applyTransform(group, child)
        parent.add(group)
        const directChildren = Array.from(child.children)
        const directGeomNames = directChildren
          .filter((element) => element.tagName === 'geom')
          .map((element) => element.getAttribute('name') ?? '')
        if (
          group.name.endsWith('_cube') ||
          directChildren.some((element) => element.tagName === 'freejoint')
        ) {
          cubes.add(group.name)
        }
        if (
          group.name.endsWith('_tray') ||
          directGeomNames.some((name) => name.endsWith('_front_rim'))
        ) {
          trays.add(group.name)
        }
        visit(child, group)
      } else if (child.tagName === 'geom') {
        if (addGeom(child, parent)) boxes += 1
      }
    }
  }
  visit(worldbody, root)
  addRobotPlaceholder(root)
  root.updateMatrixWorld(true)

  const cubeObjects = Array.from(cubes)
    .map((name) => root.getObjectByName(name))
    .filter((object): object is THREE.Object3D => Boolean(object))
  const trayObjects = Array.from(trays)
    .map((name) => root.getObjectByName(name))
    .filter((object): object is THREE.Object3D => Boolean(object))
  const flows: TaskFlowSummary[] = []

  cubeObjects.forEach((cube, index) => {
    const color = taskColor(cube.name)
    if (!color) return
    const tray = trayObjects.find((candidate) => taskColor(candidate.name)?.name === color.name)
    if (!tray) return

    const start = cube.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0, 0.055))
    const end = tray.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0, 0.075))
    const distance = start.distanceTo(end)
    const middle = start
      .clone()
      .lerp(end, 0.5)
      .add(new THREE.Vector3(0, 0, Math.max(0.12, distance * 0.34)))
    const curve = new THREE.CatmullRomCurve3([
      start,
      start.clone().lerp(middle, 0.58),
      middle,
      middle.clone().lerp(end, 0.58),
      end,
    ])
    const flowGroup = new THREE.Group()
    flowGroup.name = `task_flow_${color.name}`

    const route = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 72, 0.0042, 8, false),
      new THREE.MeshBasicMaterial({
        color: color.hex,
        transparent: true,
        opacity: 0.46,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    )
    flowGroup.add(route)

    const halo = new THREE.Mesh(
      new THREE.TubeGeometry(curve, 72, 0.009, 8, false),
      new THREE.MeshBasicMaterial({
        color: color.hex,
        transparent: true,
        opacity: 0.07,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    )
    flowGroup.add(halo)

    const packet = new THREE.Mesh(
      new THREE.SphereGeometry(0.013, 18, 12),
      new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }),
    )
    const packetGlow = new THREE.Mesh(
      new THREE.SphereGeometry(0.025, 18, 12),
      new THREE.MeshBasicMaterial({
        color: color.hex,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    )
    packet.add(packetGlow)
    flowGroup.add(packet)

    const ringMaterial = new THREE.MeshBasicMaterial({
      color: color.hex,
      transparent: true,
      opacity: 0.62,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
    const sourceRing = new THREE.Mesh(new THREE.TorusGeometry(0.034, 0.003, 8, 32), ringMaterial)
    sourceRing.position.copy(start)
    flowGroup.add(sourceRing)
    const targetRing = new THREE.Mesh(
      new THREE.TorusGeometry(0.045, 0.003, 8, 32),
      ringMaterial.clone(),
    )
    targetRing.position.copy(end)
    flowGroup.add(targetRing)

    const tangent = curve.getTangent(0.92).normalize()
    const arrow = new THREE.Mesh(
      new THREE.ConeGeometry(0.018, 0.045, 14),
      new THREE.MeshBasicMaterial({ color: color.hex, transparent: true, opacity: 0.86 }),
    )
    arrow.position.copy(curve.getPoint(0.92))
    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent)
    flowGroup.add(arrow)

    root.add(flowGroup)
    const id = `${color.name}-${index}`
    animatedFlows.push({
      id,
      curve,
      group: flowGroup,
      packet,
      sourceRing,
      targetRing,
      phase: index / Math.max(1, cubeObjects.length),
    })
    flows.push({
      id,
      label: `${cube.name.replaceAll('_', ' ')} → ${tray.name.replaceAll('_', ' ')}`,
      color: color.name,
    })
  })

  return { boxes, cubes: cubes.size, trays: trays.size, flows }
}

function OrbitCanvas({
  sceneXml,
  sceneId,
  immersive,
}: {
  sceneXml: string
  sceneId: string
  immersive: boolean
}) {
  const mountRef = useRef<HTMLDivElement>(null)
  const setViewRef = useRef<(preset: CameraPreset) => void>(() => undefined)
  const setFlowFocusRef = useRef<(flowId: string | null) => void>(() => undefined)
  const autoOrbitRef = useRef(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<SceneSummary | null>(null)
  const [cameraPreset, setCameraPreset] = useState<CameraPreset | null>('perspective')
  const [autoOrbit, setAutoOrbit] = useState(false)
  const [activeFlow, setActiveFlow] = useState<string | null>(null)

  useEffect(() => {
    autoOrbitRef.current = autoOrbit
  }, [autoOrbit])

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    setLoading(true)
    setSummary(null)
    setActiveFlow(null)
    setFlowFocusRef.current = () => undefined
    const abortController = new AbortController()
    let disposed = false
    let animationFrame = 0
    let renderer: THREE.WebGLRenderer | null = null
    let controls: OrbitControls | null = null
    let resizeObserver: ResizeObserver | null = null
    const animatedFlows: AnimatedFlow[] = []
    const animationStartedAt = Date.now()
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(immersive ? 0x080b10 : 0x0b0e13)
    scene.fog = new THREE.Fog(immersive ? 0x080b10 : 0x0b0e13, 1.6, 3.2)
    const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 10)
    camera.up.set(0, 0, 1)

    const setView = (preset: CameraPreset) => {
      const positions: Record<CameraPreset, [number, number, number]> = {
        perspective: [0.82, -0.92, 0.72],
        overhead: [0.2, -0.001, 1.42],
        side: [1.18, -0.001, 0.52],
      }
      const [x, y, z] = positions[preset]
      camera.position.set(x, y, z)
      controls?.target.set(0.2, 0, 0.32)
      controls?.update()
    }
    setViewRef.current = setView

    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
      renderer.outputColorSpace = THREE.SRGBColorSpace
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.08
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFShadowMap
      renderer.domElement.setAttribute('aria-label', `Orbit view of workcell ${sceneId}`)
      mount.appendChild(renderer.domElement)
      controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping = true
      controls.dampingFactor = 0.08
      controls.minDistance = 0.28
      controls.maxDistance = 2.8
      controls.maxPolarAngle = Math.PI * 0.49
      controls.autoRotateSpeed = 0.45
      setView('perspective')
    } catch (renderError) {
      renderer?.dispose()
      renderer?.domElement.remove()
      setError(renderError instanceof Error ? renderError.message : String(renderError))
      setLoading(false)
      return
    }

    scene.add(new THREE.HemisphereLight(0xd8efff, 0x202732, 1.8))
    const keyLight = new THREE.DirectionalLight(0xffffff, 3.2)
    keyLight.position.set(0.35, -0.65, 1.35)
    keyLight.castShadow = true
    keyLight.shadow.mapSize.set(1024, 1024)
    scene.add(keyLight)
    const rimLight = new THREE.DirectionalLight(0x56c8d8, 1.1)
    rimLight.position.set(-0.8, 0.5, 0.7)
    scene.add(rimLight)

    const grid = new THREE.GridHelper(1.8, 18, 0x2a3342, 0x1d242f)
    grid.rotation.x = Math.PI / 2
    grid.position.z = 0.004
    scene.add(grid)
    const root = new THREE.Group()
    scene.add(root)

    const resize = () => {
      if (!renderer) return
      const bounds = mount.getBoundingClientRect()
      const width = Math.max(1, Math.floor(bounds.width))
      const height = Math.max(1, Math.floor(bounds.height))
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    }
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(mount)
    resize()

    const animate = () => {
      if (disposed || !renderer) return
      if (controls) controls.autoRotate = autoOrbitRef.current
      const elapsed = reduceMotion ? 0 : (Date.now() - animationStartedAt) / 1000
      animatedFlows.forEach((flow) => {
        const progress = reduceMotion ? 0.52 : (elapsed * 0.11 + flow.phase) % 1
        flow.packet.position.copy(flow.curve.getPoint(progress))
        const sourcePulse = 1 + Math.sin(elapsed * 2.6 + flow.phase * Math.PI * 2) * 0.18
        const targetPulse = 1 + Math.sin(elapsed * 2.6 + flow.phase * Math.PI * 2 + Math.PI) * 0.16
        flow.sourceRing.scale.setScalar(sourcePulse)
        flow.targetRing.scale.setScalar(targetPulse)
      })
      controls?.update()
      renderer.render(scene, camera)
      animationFrame = requestAnimationFrame(animate)
    }
    animate()

    void fetch(mediaUrl(sceneXml), { signal: abortController.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} · compiled scene XML is not servable`)
        return response.text()
      })
      .then((xmlText) => {
        if (disposed) return
        const nextSummary = buildSceneGeometry(xmlText, root, animatedFlows)
        setSummary(nextSummary)
        setActiveFlow(null)
        setFlowFocusRef.current = (flowId) => {
          animatedFlows.forEach((flow) => {
            flow.group.visible = flowId === null || flow.id === flowId
          })
        }
        setError(null)
      })
      .catch((sceneError: unknown) => {
        if (sceneError instanceof DOMException && sceneError.name === 'AbortError') return
        setError(sceneError instanceof Error ? sceneError.message : String(sceneError))
      })
      .finally(() => {
        if (!disposed) setLoading(false)
      })

    return () => {
      disposed = true
      abortController.abort()
      cancelAnimationFrame(animationFrame)
      resizeObserver?.disconnect()
      controls?.dispose()
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments) {
          object.geometry.dispose()
          const materials = Array.isArray(object.material) ? object.material : [object.material]
          materials.forEach((material) => material.dispose())
        }
      })
      renderer?.dispose()
      renderer?.domElement.remove()
    }
  }, [immersive, sceneId, sceneXml])

  const chooseView = (preset: CameraPreset) => {
    setCameraPreset(preset)
    setAutoOrbit(false)
    setViewRef.current(preset)
  }

  const toggleAutoOrbit = () => {
    const next = !autoOrbit
    setAutoOrbit(next)
    if (next) setCameraPreset(null)
  }

  const chooseFlow = (flowId: string) => {
    const next = activeFlow === flowId ? null : flowId
    setActiveFlow(next)
    setFlowFocusRef.current(next)
  }

  return (
    <div className={immersive ? 'foundry-orbit' : 'border border-line-2 bg-bg'}>
      <div
        className={
          immersive
            ? 'foundry-orbit-toolbar'
            : 'flex flex-wrap items-center gap-2 border-b border-line px-2 py-1.5'
        }
      >
        <Led tone={error ? 'red' : loading ? 'amber' : 'green'} pulse={loading} />
        <span className="cap text-ink">scene inspection · drag orbit · wheel zoom</span>
        {summary && (
          <span className={immersive ? 'hidden items-center gap-1.5 2xl:flex' : 'ml-auto flex items-center gap-1.5'}>
            <Tag tone="dim">{summary.boxes} scene boxes</Tag>
            <Tag tone="cyan">{summary.cubes} cubes</Tag>
            <Tag tone="violet">{summary.trays} trays</Tag>
          </span>
        )}
        <span className={immersive ? 'ml-auto flex items-center gap-1' : 'flex items-center gap-1'}>
          {(['perspective', 'overhead', 'side'] as const).map((preset) => (
            <button
              key={preset}
              className={`btn ${cameraPreset === preset && !autoOrbit ? 'btn-primary' : 'btn-quiet'}`}
              type="button"
              onClick={() => chooseView(preset)}
              aria-pressed={cameraPreset === preset && !autoOrbit}
            >
              {preset === 'perspective' ? 'orbit' : preset}
            </button>
          ))}
          <button
            className={`btn ${autoOrbit ? 'btn-primary' : 'btn-quiet'}`}
            type="button"
            onClick={toggleAutoOrbit}
            aria-pressed={autoOrbit}
          >
            {autoOrbit ? 'stop sweep' : 'auto sweep'}
          </button>
        </span>
      </div>
      <div
        ref={mountRef}
        className={immersive ? 'foundry-orbit-canvas' : 'h-[420px] w-full overflow-hidden'}
        role="img"
        aria-label={`Interactive 3D orbit view for ${sceneId}`}
      />
      {immersive && summary && summary.flows.length > 0 && (
        <div className="foundry-flow-map" aria-label="Compiled task plan routes">
          <div className="foundry-flow-heading">
            <span className="foundry-flow-kicker">task plan</span>
            <strong>{summary.flows.length} color routes</strong>
            <span>visual intent only · not an executed trajectory</span>
          </div>
          <div className="foundry-flow-list">
            {summary.flows.map((flow) => (
              <button
                key={flow.id}
                type="button"
                className={`foundry-flow-route flow-${flow.color} ${activeFlow === flow.id ? 'active' : ''}`}
                onClick={() => chooseFlow(flow.id)}
                aria-pressed={activeFlow === flow.id}
              >
                <span className="foundry-flow-route-line" aria-hidden>
                  <i />
                </span>
                <span>{flow.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
      {immersive && loading && (
        <div className="foundry-orbit-loading">
          <Led tone="cyan" pulse />
          <span className="cap text-cyan">compiling scene view</span>
        </div>
      )}
      {error && <p className="border-t border-red/40 p-2 font-mono text-2xs text-red">{error}</p>}
    </div>
  )
}

export default function WorkcellOrbit({
  sceneXml,
  sceneId,
  immersive = false,
}: {
  sceneXml: string
  sceneId: string
  immersive?: boolean
}) {
  return <OrbitCanvas sceneXml={sceneXml} sceneId={sceneId} immersive={immersive} />
}
