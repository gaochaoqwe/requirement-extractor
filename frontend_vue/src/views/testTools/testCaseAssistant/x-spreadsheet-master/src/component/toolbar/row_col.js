import Dropdown from '../dropdown';
import { h } from '../element';
import { cssPrefix } from '../../config';
import Item from './item';

class DropdownRowCol extends Dropdown {
  constructor(onChange) {
    // showArrow=true 让它和 Normal/Arial 一样显示向下箭头
    super('行和列', '220px', true, 'bottom-left');
    this.onRowColChange = onChange;
    this._buildContent();
  }

  _buildContent() {
    const self = this;

    const makeRow = (label, placeholder, applyFn) => {
      const input = h('input', `${cssPrefix}-rowcol-input`)
        .attr('type', 'number')
        .attr('placeholder', placeholder)
        .css('width', '80px')
        .css('margin-left', '8px')
        .css('border', '1px solid #d1d5db')
        .css('border-radius', '4px')
        .css('padding', '2px 6px')
        .css('font-size', '12px');

      const btn = h('button', `${cssPrefix}-rowcol-btn`)
        .css('margin-left', '6px')
        .css('padding', '2px 10px')
        .css('border', '1px solid #3b82f6')
        .css('border-radius', '4px')
        .css('background', '#3b82f6')
        .css('color', '#fff')
        .css('font-size', '12px')
        .css('cursor', 'pointer')
        .child('确定')
        .on('click', () => {
          const val = parseInt(input.el.value, 10);
          if (!Number.isNaN(val) && val > 0) {
            applyFn(val);
            input.el.value = '';
            self.hide();
          }
        });

      return h('div', `${cssPrefix}-rowcol-row`)
        .css('display', 'flex')
        .css('align-items', 'center')
        .css('padding', '8px 10px')
        .children(
          h('span', '').css('font-size', '12px').css('color', '#374151').css('min-width', '54px').child(label),
          input,
          btn,
        );
    };

    const divider = h('div', '')
      .css('border-top', '1px solid #e5e7eb')
      .css('margin', '2px 0');

    const rowHeightRow = makeRow('行高 (px)', '例：25', (val) => {
      self.onRowColChange('rowHeight', val);
    });
    const colWidthRow = makeRow('列宽 (px)', '例：100', (val) => {
      self.onRowColChange('colWidth', val);
    });

    this.setContentChildren(rowHeightRow, divider, colWidthRow);
    this.contentEl.css('padding', '4px 0');
  }

  // 覆盖 setTitle，避免父类用数值覆盖文字标题
  setTitle() {}
}

export default class RowCol extends Item {
  constructor(onChange) {
    super();
    this.onChangeFn = onChange;
  }

  element() {
    this.dd = new DropdownRowCol(this.onChangeFn);
    return super.element()
      .css('padding', '0 2px')
      .child(this.dd);
  }

  setState() {}
}
