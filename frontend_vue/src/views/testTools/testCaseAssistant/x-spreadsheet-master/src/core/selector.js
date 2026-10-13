import { CellRange } from './cell_range';

export default class Selector {
  constructor() {
    this.range = new CellRange(0, 0, 0, 0);
    this.ri = 0;
    this.ci = 0;
  }

  multiple() {
    if (typeof this.range.multiple === 'function') {
      return this.range.multiple();
    }
    // range 是 plain object 时降级计算
    const { sri = 0, sci = 0, eri = 0, eci = 0 } = this.range;
    return eri - sri > 0 || eci - sci > 0;
  }

  setIndexes(ri, ci) {
    this.ri = ri;
    this.ci = ci;
  }

  size() {
    return this.range.size();
  }
}
