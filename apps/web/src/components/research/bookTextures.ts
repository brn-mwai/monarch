import * as THREE from 'three';

const LOCKED_WIDTH = 900;

function seeded(seed: number) {
  let state = seed % 2147483647 || 1;
  return () => {
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
}

export function paperGrain() {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  if (context) {
    const image = context.createImageData(size, size);
    const random = seeded(7);
    for (let index = 0; index < size * size; index += 1) {
      const value = 118 + random() * 20;
      image.data.set([value, value, value, 255], index * 4);
    }
    context.putImageData(image, 0, 0);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(4, 6);
  return texture;
}

export function stripeEdge() {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext('2d');
  if (context) {
    context.fillStyle = '#efe9dc';
    context.fillRect(0, 0, size, size);
    const random = seeded(11);
    for (let line = 0; line < size; line += 2) {
      const shade = 200 + Math.floor(random() * 30);
      context.fillStyle = `rgba(${shade}, ${shade - 6}, ${shade - 16}, 0.55)`;
      context.fillRect(line, 0, 1, size);
      context.fillRect(0, line, size, 1);
    }
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function lockIcon(context: CanvasRenderingContext2D, x: number, y: number, size: number) {
  context.save();
  context.strokeStyle = '#6b1c2a';
  context.fillStyle = '#6b1c2a';
  context.lineWidth = size * 0.1;
  context.beginPath();
  context.arc(x, y - size * 0.18, size * 0.26, Math.PI, 0);
  context.stroke();
  context.fillRect(x - size * 0.38, y - size * 0.18, size * 0.76, size * 0.6);
  context.fillStyle = '#f7f3ea';
  context.beginPath();
  context.arc(x, y + size * 0.05, size * 0.08, 0, Math.PI * 2);
  context.fill();
  context.fillRect(x - size * 0.03, y + size * 0.05, size * 0.06, size * 0.17);
  context.restore();
}

export function drawLockedPage(page: number, label: string, aspect: number) {
  const width = LOCKED_WIDTH;
  const height = Math.round(width * aspect);
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) return canvas;

  context.fillStyle = '#f7f3ea';
  context.fillRect(0, 0, width, height);

  const random = seeded(page * 97 + 13);
  const marginX = width * 0.14;
  const lineHeight = height * 0.024;
  context.filter = 'blur(2px)';
  context.fillStyle = 'rgba(40, 36, 30, 0.13)';
  for (let y = height * 0.1; y < height * 0.86; y += lineHeight) {
    if (random() < 0.08) {
      y += lineHeight;
      continue;
    }
    const lineWidth = (width - marginX * 2) * (random() < 0.15 ? 0.3 + random() * 0.4 : 0.92 + random() * 0.08);
    context.fillRect(marginX, y, lineWidth, lineHeight * 0.34);
  }
  context.filter = 'none';

  const cardWidth = width * 0.64;
  const cardHeight = height * 0.2;
  const cardX = (width - cardWidth) / 2;
  const cardY = height * 0.4;
  context.fillStyle = 'rgba(247, 243, 234, 0.96)';
  context.strokeStyle = 'rgba(107, 28, 42, 0.35)';
  context.lineWidth = 2;
  context.beginPath();
  if (typeof context.roundRect === 'function') context.roundRect(cardX, cardY, cardWidth, cardHeight, 18);
  else context.rect(cardX, cardY, cardWidth, cardHeight);
  context.fill();
  context.stroke();

  lockIcon(context, width / 2, cardY + cardHeight * 0.28, width * 0.07);
  context.fillStyle = '#2a2420';
  context.textAlign = 'center';
  context.font = `600 ${Math.round(width * 0.03)}px Georgia, 'Times New Roman', serif`;
  context.fillText('Available in full at the CUEA Library', width / 2, cardY + cardHeight * 0.66);
  context.fillStyle = '#6f675d';
  context.font = `${Math.round(width * 0.024)}px Georgia, 'Times New Roman', serif`;
  context.fillText('This preview shows selected pages only', width / 2, cardY + cardHeight * 0.84);

  context.fillStyle = '#4a433b';
  context.font = `${Math.round(width * 0.024)}px Georgia, 'Times New Roman', serif`;
  context.fillText(label, width / 2, height * 0.94);
  return canvas;
}
