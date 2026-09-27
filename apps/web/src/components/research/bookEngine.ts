import * as THREE from 'three';

import { drawLockedPage, paperGrain, stripeEdge } from './bookTextures';
import { playFlip } from './flipSound';

export interface OutlineEntry {
  level: number;
  title: string;
  page: number;
}

export interface BookMeta {
  pages: number;
  aspect: number;
  labels: string[];
  preview: number[];
  blank: number[];
  outline: OutlineEntry[];
}

export interface BookState {
  flipped: number;
  total: number;
  left: number | null;
  right: number | null;
  side: 'left' | 'right' | null;
}

const PAGE_W = 1;
const SEGMENTS = 48;
const LEAF_T = 0.0024;
const COVER_T = 0.02;
const COVER_PAD = 0.035;
const FLIP_MS = 950;
const FAST_FLIP_MS = 260;
const FAST_STAGGER_MS = 70;
const CURL = 1.05;
const TILT = 0.28;
const PAPER = new THREE.Color('#fbf8f1');
const ENDPAPER = new THREE.Color('#efe6d4');
const CLOTH = new THREE.Color('#5c1724');
const ASSET_ROOT = '/research/book';

interface Flip {
  from: number;
  to: number;
  start: number;
  duration: number;
  direction: 1 | -1;
  zFrom: number;
  zTo: number;
}

interface Leaf {
  index: number;
  pivot: THREE.Group;
  geometry: THREE.PlaneGeometry | null;
  front: THREE.Mesh | null;
  back: THREE.Mesh | null;
  frontPage: number | null;
  backPage: number | null;
  angle: number;
  flip: Flip | null;
  textured: boolean;
}

function frameWidth(flipped: number, total: number) {
  return flipped === 0 || flipped === total ? PAGE_W + COVER_PAD * 2 : 2 * (PAGE_W + COVER_PAD) + 0.08;
}

function frameCentre(flipped: number, total: number) {
  if (flipped === 0) return PAGE_W / 2;
  if (flipped === total) return -PAGE_W / 2;
  return 0;
}

function easeInOut(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export class BookEngine {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(32, 1, 0.05, 40);
  private readonly book = new THREE.Group();
  private readonly leaves: Leaf[] = [];
  private readonly pageHeight: number;
  private readonly paperCount: number;
  private readonly total: number;
  private readonly textureCache = new Map<number, THREE.Texture>();
  private readonly loader = new THREE.TextureLoader();
  private readonly grain: THREE.Texture;
  private readonly edgeTexture: THREE.Texture;
  private readonly rightBlock: THREE.Mesh;
  private readonly leftBlock: THREE.Mesh;
  private readonly preview: Set<number>;
  private readonly blank: Set<number>;
  private readonly resizeObserver: ResizeObserver;
  private flipped = 0;
  private queue: number[] = [];
  private queueTimer = 0;
  private frame = 0;
  private zoom = 1;
  private pointer = new THREE.Vector2();
  private centre = PAGE_W / 2;
  private width = frameWidth(0, 1);
  private muted = false;
  private narrow = false;
  private side: 'left' | 'right' = 'right';
  private disposed = false;

  constructor(
    private readonly container: HTMLElement,
    private readonly meta: BookMeta,
    private readonly onChange: (state: BookState) => void,
  ) {
    this.pageHeight = PAGE_W * meta.aspect;
    this.paperCount = Math.ceil(meta.pages / 2);
    this.total = this.paperCount + 1;
    this.width = frameWidth(0, this.total);
    this.preview = new Set(meta.preview);
    this.blank = new Set(meta.blank);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    container.appendChild(this.renderer.domElement);

    this.grain = paperGrain();
    this.edgeTexture = stripeEdge();

    this.scene.add(new THREE.HemisphereLight(0xfff6ea, 0x1a1414, 1.15));
    const key = new THREE.DirectionalLight(0xfff3e0, 1.6);
    key.position.set(-1.6, 1.2, 3.2);
    key.castShadow = true;
    const compact = Math.min(window.innerWidth, window.innerHeight) < 700;
    key.shadow.mapSize.set(compact ? 1024 : 2048, compact ? 1024 : 2048);
    key.shadow.camera.left = -2;
    key.shadow.camera.right = 2;
    key.shadow.camera.top = 1.6;
    key.shadow.camera.bottom = -1.6;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 8;
    key.shadow.bias = -0.0002;
    key.shadow.normalBias = 0.02;
    key.shadow.radius = 4;
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(0xdfe8ff, 0.35);
    fill.position.set(2, -1, 2);
    this.scene.add(fill);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(8, 8),
      new THREE.ShadowMaterial({ opacity: 0.42 }),
    );
    ground.position.z = -COVER_T * 1.1;
    ground.receiveShadow = true;
    this.book.add(ground);

    this.rightBlock = this.makeBlock();
    this.leftBlock = this.makeBlock();
    this.book.add(this.rightBlock, this.leftBlock);

    this.book.add(this.makeBackCover());
    this.book.rotation.x = -TILT;
    this.scene.add(this.book);

    for (let index = 0; index < this.total; index += 1) {
      this.leaves.push(index === 0 ? this.makeCover() : this.makeLeaf(index));
    }
    this.layoutAll();

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
    this.emit();
    this.loop();
  }

  next() {
    const target = this.target();
    if (this.narrow && !this.queue.length && this.isOpen(target) && this.side === 'left') {
      this.side = 'right';
      this.emit();
      return;
    }
    const nextValue = Math.min(target + 1, this.total);
    this.side = nextValue >= 2 ? 'left' : 'right';
    this.enqueue(nextValue);
  }

  prev() {
    const target = this.target();
    if (this.narrow && !this.queue.length && this.isOpen(target) && this.side === 'right' && target >= 2) {
      this.side = 'left';
      this.emit();
      return;
    }
    this.side = 'right';
    this.enqueue(Math.max(target - 1, 0));
  }

  first() {
    this.side = 'right';
    this.enqueue(0);
  }

  last() {
    this.side = 'right';
    this.enqueue(this.total);
  }

  goToPage(page: number) {
    const leaf = Math.ceil(page / 2);
    this.side = page % 2 === 1 ? 'right' : 'left';
    this.enqueue(page % 2 === 1 ? leaf : leaf + 1);
    this.emit();
  }

  setMuted(muted: boolean) {
    this.muted = muted;
  }

  setPointer(x: number, y: number) {
    this.pointer.set(x, y);
  }

  zoomBy(factor: number) {
    this.zoom = THREE.MathUtils.clamp(this.zoom * factor, 0.55, 1.7);
  }

  dispose() {
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    window.clearTimeout(this.queueTimer);
    this.resizeObserver.disconnect();
    this.scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => material.dispose());
      }
    });
    this.textureCache.forEach((texture) => texture.dispose());
    this.grain.dispose();
    this.edgeTexture.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }

  private isOpen(flipped: number) {
    return flipped > 0 && flipped < this.total;
  }

  private target() {
    return this.queue.length ? this.queue[this.queue.length - 1] : this.flipped;
  }

  private enqueue(targetFlipped: number) {
    const from = this.target();
    if (targetFlipped === from) return;
    const step = targetFlipped > from ? 1 : -1;
    for (let value = from + step; step > 0 ? value <= targetFlipped : value >= targetFlipped; value += step) {
      this.queue.push(value);
    }
    if (!this.queueTimer) this.drain();
  }

  private drain() {
    const nextValue = this.queue.shift();
    if (nextValue === undefined) {
      this.queueTimer = 0;
      return;
    }
    const fast = this.queue.length > 0;
    const forward = nextValue > this.flipped;
    const leafIndex = forward ? this.flipped : nextValue;
    this.startFlip(this.leaves[leafIndex], forward, fast);
    this.flipped = nextValue;
    this.ensureTextures();
    this.emit();
    this.queueTimer = window.setTimeout(() => this.drain(), fast ? FAST_STAGGER_MS : FLIP_MS * 0.55);
  }

  private startFlip(leaf: Leaf, forward: boolean, fast: boolean) {
    const duration = fast ? FAST_FLIP_MS : FLIP_MS;
    leaf.flip = {
      from: leaf.angle,
      to: forward ? Math.PI : 0,
      start: performance.now(),
      duration,
      direction: forward ? 1 : -1,
      zFrom: leaf.pivot.position.z,
      zTo: this.restZ(leaf.index, forward),
    };
    if (!this.muted) playFlip(fast);
  }

  private restZ(index: number, onLeft: boolean) {
    if (index === 0) {
      return onLeft ? COVER_T / 2 - COVER_T : (this.paperCount + 1) * LEAF_T + COVER_T / 2;
    }
    return onLeft ? index * LEAF_T : (this.paperCount - index + 1) * LEAF_T;
  }

  private makeBlock() {
    const materials = [
      new THREE.MeshStandardMaterial({ map: this.edgeTexture, roughness: 0.95 }),
      new THREE.MeshStandardMaterial({ map: this.edgeTexture, roughness: 0.95 }),
      new THREE.MeshStandardMaterial({ map: this.edgeTexture, roughness: 0.95 }),
      new THREE.MeshStandardMaterial({ map: this.edgeTexture, roughness: 0.95 }),
      new THREE.MeshStandardMaterial({ color: PAPER, roughness: 0.95 }),
      new THREE.MeshStandardMaterial({ color: PAPER, roughness: 0.95 }),
    ];
    const block = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), materials);
    block.castShadow = true;
    block.receiveShadow = true;
    return block;
  }

  private layoutBlocks() {
    const leftCount = Math.max(this.flipped - 1, 0);
    const rightCount = Math.max(this.paperCount - Math.max(this.flipped - 1, 0), 0);
    const inset = 0.006;
    this.setBlock(this.rightBlock, rightCount, inset);
    this.setBlock(this.leftBlock, leftCount, -PAGE_W + inset);
  }

  private setBlock(block: THREE.Mesh, count: number, left: number) {
    const depth = Math.max(count - 1.5, 0) * LEAF_T;
    block.visible = depth > 0;
    if (!block.visible) return;
    block.scale.set(PAGE_W - 0.012, this.pageHeight - 0.006, depth);
    block.position.set(left + (PAGE_W - 0.012) / 2, 0, depth / 2);
  }

  private makeBackCover() {
    const width = PAGE_W + COVER_PAD;
    const height = this.pageHeight + COVER_PAD * 2;
    const back = this.loadStatic(`${ASSET_ROOT}/cover_back.png`);
    const materials = [
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: ENDPAPER, roughness: 0.9, bumpMap: this.grain, bumpScale: 0.6 }),
      new THREE.MeshStandardMaterial({ map: back, roughness: 0.8 }),
    ];
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, COVER_T), materials);
    mesh.position.set(width / 2, 0, -COVER_T / 2);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  private makeCover(): Leaf {
    const width = PAGE_W + COVER_PAD;
    const height = this.pageHeight + COVER_PAD * 2;
    const front = this.loadStatic(`${ASSET_ROOT}/cover_front.png`);
    const spine = this.loadStatic(`${ASSET_ROOT}/spine.png`);
    const materials = [
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ map: spine, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ color: CLOTH, roughness: 0.85 }),
      new THREE.MeshStandardMaterial({ map: front, roughness: 0.78, bumpMap: this.grain, bumpScale: 0.4 }),
      new THREE.MeshStandardMaterial({ color: ENDPAPER, roughness: 0.9, bumpMap: this.grain, bumpScale: 0.6 }),
    ];
    const geometry = new THREE.BoxGeometry(width, height, COVER_T);
    geometry.translate(width / 2, 0, 0);
    const mesh = new THREE.Mesh(geometry, materials);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    const pivot = new THREE.Group();
    pivot.add(mesh);
    this.book.add(pivot);
    return { index: 0, pivot, geometry: null, front: mesh, back: null, frontPage: null, backPage: null, angle: 0, flip: null, textured: true };
  }

  private makeLeaf(index: number): Leaf {
    const geometry = new THREE.PlaneGeometry(PAGE_W, this.pageHeight, SEGMENTS, 1);
    geometry.translate(PAGE_W / 2, 0, 0);
    const frontPage = 2 * index - 1;
    const backPage = 2 * index <= this.meta.pages ? 2 * index : null;
    const front = new THREE.Mesh(
      geometry,
      new THREE.MeshStandardMaterial({ color: PAPER, roughness: 0.92, bumpMap: this.grain, bumpScale: 0.35, side: THREE.FrontSide }),
    );
    const back = new THREE.Mesh(
      geometry,
      new THREE.MeshStandardMaterial({ color: PAPER, roughness: 0.92, bumpMap: this.grain, bumpScale: 0.35, side: THREE.BackSide }),
    );
    for (const mesh of [front, back]) {
      mesh.castShadow = true;
      mesh.receiveShadow = true;
    }
    const pivot = new THREE.Group();
    pivot.add(front, back);
    this.book.add(pivot);
    return { index, pivot, geometry, front, back, frontPage, backPage, angle: 0, flip: null, textured: false };
  }

  private layoutAll() {
    for (const leaf of this.leaves) {
      const onLeft = leaf.index < this.flipped;
      leaf.angle = onLeft ? Math.PI : 0;
      leaf.pivot.position.z = this.restZ(leaf.index, onLeft);
      this.shapeLeaf(leaf, leaf.angle, 0);
    }
    this.layoutBlocks();
    this.ensureTextures();
  }

  private shapeLeaf(leaf: Leaf, angle: number, curl: number) {
    if (leaf.index === 0 || !leaf.geometry) {
      leaf.pivot.rotation.y = -angle;
      return;
    }
    const position = leaf.geometry.attributes.position as THREE.BufferAttribute;
    const step = PAGE_W / SEGMENTS;
    const xs: number[] = [0];
    const zs: number[] = [0];
    for (let column = 1; column <= SEGMENTS; column += 1) {
      const along = (column - 0.5) / SEGMENTS;
      const bend = angle - curl * along * along;
      xs.push(xs[column - 1] + Math.cos(bend) * step);
      zs.push(zs[column - 1] + Math.sin(bend) * step);
    }
    const columns = SEGMENTS + 1;
    for (let row = 0; row < 2; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const vertex = row * columns + column;
        position.setX(vertex, xs[column]);
        position.setZ(vertex, zs[column]);
      }
    }
    position.needsUpdate = true;
    leaf.geometry.computeVertexNormals();
    leaf.geometry.computeBoundingSphere();
  }

  private ensureTextures() {
    const low = Math.max(this.flipped - 3, 1);
    const high = Math.min(this.flipped + 3, this.paperCount);
    for (let index = low; index <= high; index += 1) {
      const leaf = this.leaves[index];
      if (leaf.textured) continue;
      leaf.textured = true;
      this.applyPage(leaf.front, leaf.frontPage, false);
      this.applyPage(leaf.back, leaf.backPage, true);
    }
  }

  private applyPage(mesh: THREE.Mesh | null, page: number | null, mirrored: boolean) {
    if (!mesh || page === null || this.blank.has(page)) return;
    const material = mesh.material as THREE.MeshStandardMaterial;
    const assign = (texture: THREE.Texture) => {
      const copy = mirrored ? texture.clone() : texture;
      if (mirrored) {
        copy.wrapS = THREE.RepeatWrapping;
        copy.repeat.x = -1;
        copy.offset.x = 1;
        copy.needsUpdate = true;
      }
      material.map = copy;
      material.needsUpdate = true;
    };
    const cached = this.textureCache.get(page);
    if (cached) {
      assign(cached);
      return;
    }
    if (this.preview.has(page)) {
      this.loader.load(`${ASSET_ROOT}/pages/p${String(page).padStart(3, '0')}.webp`, (texture) => {
        if (this.disposed) return;
        this.prepare(texture);
        this.textureCache.set(page, texture);
        assign(texture);
      });
      return;
    }
    const texture = new THREE.CanvasTexture(drawLockedPage(page, this.meta.labels[page - 1] ?? String(page), this.meta.aspect));
    this.prepare(texture);
    this.textureCache.set(page, texture);
    assign(texture);
  }

  private prepare(texture: THREE.Texture) {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
  }

  private loadStatic(url: string) {
    const texture = this.loader.load(url);
    this.prepare(texture);
    return texture;
  }

  private resize() {
    const { clientWidth, clientHeight } = this.container;
    if (!clientWidth || !clientHeight) return;
    this.renderer.setSize(clientWidth, clientHeight, false);
    this.camera.aspect = clientWidth / clientHeight;
    this.camera.updateProjectionMatrix();
    const narrow = this.camera.aspect < 0.85 || clientWidth < 520;
    if (narrow !== this.narrow) {
      this.narrow = narrow;
      this.emit();
    }
  }

  private placeCamera() {
    const single = this.narrow && this.isOpen(this.flipped);
    const targetWidth = single ? PAGE_W + COVER_PAD * 2 : frameWidth(this.flipped, this.total);
    const sideCentre = this.side === 'left' ? -PAGE_W / 2 : PAGE_W / 2;
    const targetCentre = single ? sideCentre : frameCentre(this.flipped, this.total);
    this.width += (targetWidth - this.width) * 0.08;
    this.centre += (targetCentre - this.centre) * 0.08;
    const halfFov = THREE.MathUtils.degToRad(this.camera.fov / 2);
    const fitHeight = (this.pageHeight + COVER_PAD * 2) * 1.22 / (2 * Math.tan(halfFov));
    const fitWidth = this.width * 1.16 / (2 * Math.tan(halfFov) * this.camera.aspect);
    const distance = Math.max(fitHeight, fitWidth) / this.zoom;
    const sway = 0.05;
    this.camera.position.set(
      this.centre + this.pointer.x * sway,
      -distance * Math.sin(0.08) + this.pointer.y * sway,
      distance,
    );
    this.camera.lookAt(this.centre, 0, 0);
  }

  private animate(now: number) {
    let moving = false;
    for (const leaf of this.leaves) {
      const flip = leaf.flip;
      if (!flip) continue;
      moving = true;
      const t = Math.min((now - flip.start) / flip.duration, 1);
      const eased = easeInOut(t);
      leaf.angle = flip.from + (flip.to - flip.from) * eased;
      const curl = CURL * Math.sin(Math.PI * eased) * flip.direction;
      leaf.pivot.position.z = flip.zFrom + (flip.zTo - flip.zFrom) * eased + Math.sin(Math.PI * eased) * 0.02;
      this.shapeLeaf(leaf, leaf.angle, curl);
      if (t >= 1) {
        leaf.flip = null;
        leaf.angle = flip.to;
        leaf.pivot.position.z = flip.zTo;
        this.shapeLeaf(leaf, leaf.angle, 0);
        this.layoutBlocks();
      }
    }
    if (moving) this.layoutBlocks();
  }

  private loop = () => {
    if (this.disposed) return;
    this.animate(performance.now());
    this.placeCamera();
    this.renderer.render(this.scene, this.camera);
    this.frame = requestAnimationFrame(this.loop);
  };

  private emit() {
    const f = this.flipped;
    const left = f >= 2 ? this.leaves[f - 1].backPage : null;
    const right = f >= 1 && f < this.total ? this.leaves[f].frontPage : null;
    const side = this.narrow && this.isOpen(f) ? (left === null && f < 2 ? 'right' : this.side) : null;
    this.onChange({ flipped: f, total: this.total, left, right, side });
  }
}
