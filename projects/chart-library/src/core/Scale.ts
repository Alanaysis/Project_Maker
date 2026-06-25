/**
 * 比例尺系统
 */

export interface Scale {
  domain: [number, number];
  range: [number, number];
  scale(value: number): number;
  invert(pixel: number): number;
}

/**
 * 线性比例尺
 */
export class LinearScale implements Scale {
  domain: [number, number];
  range: [number, number];

  constructor(domain: [number, number], range: [number, number]) {
    this.domain = domain;
    this.range = range;
  }

  scale(value: number): number {
    const [d0, d1] = this.domain;
    const [r0, r1] = this.range;

    if (d1 - d0 === 0) {
      return (r0 + r1) / 2;
    }

    return r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
  }

  invert(pixel: number): number {
    const [d0, d1] = this.domain;
    const [r0, r1] = this.range;

    if (r1 - r0 === 0) {
      return (d0 + d1) / 2;
    }

    return d0 + ((pixel - r0) / (r1 - r0)) * (d1 - d0);
  }

  getTicks(count: number = 5): number[] {
    const [min, max] = this.domain;
    const range = max - min;
    const roughStep = range / count;
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const residual = roughStep / magnitude;

    let niceStep: number;
    if (residual <= 1.5) niceStep = magnitude;
    else if (residual <= 3) niceStep = 2 * magnitude;
    else if (residual <= 7) niceStep = 5 * magnitude;
    else niceStep = 10 * magnitude;

    const niceMin = Math.floor(min / niceStep) * niceStep;
    const niceMax = Math.ceil(max / niceStep) * niceStep;

    const ticks: number[] = [];
    for (let tick = niceMin; tick <= niceMax + niceStep * 0.5; tick += niceStep) {
      ticks.push(parseFloat(tick.toPrecision(12)));
    }

    return ticks;
  }
}

/**
 * 分类比例尺
 */
export class CategoryScale {
  domain: string[];
  range: [number, number];

  constructor(domain: string[], range: [number, number]) {
    this.domain = domain;
    this.range = range;
  }

  scale(index: number): number {
    const [r0, r1] = this.range;
    const step = (r1 - r0) / this.domain.length;
    return r0 + step * (index + 0.5);
  }

  getIndex(value: number): number {
    const [r0, r1] = this.range;
    const step = (r1 - r0) / this.domain.length;
    const index = Math.floor((value - r0) / step);
    return Math.max(0, Math.min(index, this.domain.length - 1));
  }

  getBandwidth(): number {
    const [r0, r1] = this.range;
    return (r1 - r0) / this.domain.length;
  }
}
