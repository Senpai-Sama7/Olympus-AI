import { createHash } from 'crypto';
export const DIM = 768;

function tokenize(text: string): string[] {
  return text.toLowerCase().split(/\s+/).filter(Boolean);
}

function signedBucket(token: string): [number, number] {
  const h = createHash('sha256').update(token).digest();
  const idx = h.readUInt32BE(0) % DIM;
  const sign = (h[4] & 0x80) ? 1.0 : -1.0;
  return [idx, sign];
}

export function embed(text: string): number[] {
  const vec = new Array<number>(DIM).fill(0);
  for (const tok of tokenize(text)) {
    const [i, s] = signedBucket(tok);
    vec[i] += s;
  }
  const norm = Math.sqrt(vec.reduce((a,b)=>a+b*b, 0)) || 1.0;
  return vec.map(v => v / norm);
}
