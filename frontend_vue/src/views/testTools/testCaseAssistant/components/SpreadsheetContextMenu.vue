<template>
  <div
    v-if="visible"
    class="custom-contextmenu"
    :style="{ left: x + 'px', top: y + 'px' }"
    @contextmenu.prevent
  >
    <div v-if="showReq" class="cm-group">
      <div class="cm-group-title" title="用于需求设计相关能力">需求设计</div>
      <div class="cm-item has-sub" title="基于当前表格内容进行需求设计（占位）">
        <div class="cm-item-row" @click.stop>
          <span>需求设计</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="初始化需求设计（占位）" @click="emitAction('req_design_init')">初始化</div>
          <div class="cm-item" title="通用功能（占位）" @click="emitAction('req_design_common')">通用功能</div>
          <div class="cm-item" title="自检测需求设计（占位）" @click="emitAction('req_design_selfcheck')">自检测</div>
          <div class="cm-item" title="接口测试需求设计（占位）" @click="emitAction('req_design_api_test')">接口测试</div>
        </div>
      </div>
      <div class="cm-item has-sub" title="对测试项进行扩展（占位）">
        <div class="cm-item-row" @click.stop>
          <span>测试项扩展</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="扩展新增性能测试项" @click="emitAction('req_expand_perf')">扩展新增性能测试项</div>
          <div class="cm-item" title="扩展新增边界测试项" @click="emitAction('req_expand_boundary')">扩展新增边界测试项</div>
        </div>
      </div>

      <div class="cm-item has-sub" title="对选中行进行组织资产复用（回填T/U列）">
        <div class="cm-item-row" @click.stop>
          <span>组织资产复用</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="对选中行进行组织资产复用（回填T/U列）" @click="emitAction('asset_reuse_selected')">组织资产复用</div>
        </div>
      </div>

      <div class="cm-item has-sub" title="对选中需求分析行进行智能填充">
        <div class="cm-item-row" @click.stop>
          <span>表单智能填充</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="根据测试用例单内容自动生成测试项描述和测试方法" @click="emitAction('case_fill_test_item_desc_method')">测试项描述和测试方法</div>
        </div>
      </div>
    </div>

    <div v-if="showReq && showCase" class="cm-divider"></div>

    <div v-if="showCase" class="cm-group">
      <div class="cm-group-title" title="用于用例设计相关能力">用例设计</div>

      <div class="cm-item has-sub" title="对已有需求分析和用例模板进行智能分析和扩展（占位）">
        <div class="cm-item-row" @click.stop>
          <span>用例设计</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="初始化用例设计（占位）" @click="emitAction('case_design_init')">初始化</div>
          <div class="cm-item" title="通用功能（占位）" @click="emitAction('case_design_common')">通用功能</div>
          <div class="cm-item has-sub" title="自检测用例设计（占位）">
            <div class="cm-item-row" @click.stop>
              <span>自检测</span>
              <span class="cm-arrow">▶</span>
            </div>
            <div class="cm-submenu">
              <div class="cm-item" title="用例裂变（占位）" @click="emitAction('case_design_selfcheck_fission')">用例裂变</div>
              <div class="cm-item" title="用例编写（占位）" @click="emitAction('case_design_selfcheck_write')">用例编写</div>
            </div>
          </div>
          <div class="cm-item has-sub" title="接口测试用例设计（占位）">
            <div class="cm-item-row" @click.stop>
              <span>接口测试</span>
              <span class="cm-arrow">▶</span>
            </div>
            <div class="cm-submenu">
              <div class="cm-item" title="复用其他功能用例（占位）" @click="emitAction('case_design_if_reuse_other')">复用其他功能用例</div>
              <div class="cm-item" title="接口异常测试（占位）" @click="emitAction('case_design_if_exception_test')">接口异常测试</div>
              <div class="cm-item" title="接口周期（占位）" @click="emitAction('case_design_if_period')">接口周期</div>
            </div>
          </div>
        </div>
      </div>

      <div class="cm-item has-sub" title="对用例进行扩展（占位）">
        <div class="cm-item-row" @click.stop>
          <span>用例扩展</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="扩展新增性能测试用例" @click="emitAction('case_expand_perf')">扩展新增性能测试用例</div>
          <div class="cm-item" title="扩展新增边界测试用例" @click="emitAction('case_expand_boundary')">扩展新增边界测试用例</div>
        </div>
      </div>

      <div class="cm-item" title="对选中行进行组织资产复用（回填I/L/P/Q列）" @click="emitAction('asset_reuse_selected_case')">组织资产复用</div>

      <div class="cm-item has-sub" title="对选中行进行智能填充">
        <div class="cm-item-row" @click.stop>
          <span>表单智能填充</span>
          <span class="cm-arrow">▶</span>
        </div>
        <div class="cm-submenu">
          <div class="cm-item" title="智能生成测试用例名称（回填I列）" @click="emitAction('case_fill_case_name')">测试用例名称</div>
          <div class="cm-item" title="按H列测试标识生成并回填J列测试用例编号" @click="emitAction('case_fill_case_id')">测试用例编号</div>
          <div class="cm-item" title="智能生成测试描述（回填L列）" @click="emitAction('case_fill_test_desc')">测试描述</div>
          <div class="cm-item" title="智能填充测试人员（占位）" @click="emitAction('case_fill_tester')">测试人员</div>
          <div class="cm-item" title="智能填充测试时间（占位）" @click="emitAction('case_fill_test_time')">测试时间</div>
        </div>
      </div>
    </div>

    <div v-if="showReq || showCase" class="cm-divider"></div>

    <div class="cm-group">
      <div class="cm-group-title" title="表格基础操作">表格操作</div>
      <div class="cm-item" title="删除当前选中行" @click="emitAction('sheet_delete_row')">删除行</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, required: true },
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  scope: { type: String, default: 'case' },
})

const emit = defineEmits(['action'])

const emitAction = (key) => {
  emit('action', key)
}

const showReq = computed(() => props.scope === 'req')
const showCase = computed(() => props.scope === 'case')
</script>

<style scoped>
.custom-contextmenu {
  position: fixed;
  z-index: 9999;
  min-width: 240px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  font-size: 13px;
  color: #111827;
}

.cm-group-title {
  padding: 6px 10px;
  font-weight: 600;
  color: #374151;
}

.cm-item {
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  position: relative;
}

.cm-item:hover {
  background: #f3f4f6;
}

.cm-divider {
  height: 1px;
  background: #e5e7eb;
  margin: 6px 0;
}

.cm-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cm-arrow {
  color: #6b7280;
  font-size: 12px;
}

.has-sub {
  padding: 0;
  position: relative;
}

/*
 * 修复二级菜单闪烁：子菜单与父菜单之间有间隙时，鼠标移动会短暂离开 .has-sub，导致 :hover 失效。
 * 在右侧加一个透明“桥接区域”覆盖间隙，保证 hover 连续。
 */
.has-sub::after {
  content: '';
  position: absolute;
  top: 0;
  right: -8px;
  width: 8px;
  height: 100%;
}

.has-sub > .cm-item-row {
  padding: 6px 10px;
}

.has-sub:hover {
  background: #f3f4f6;
}

.cm-submenu {
  display: none;
  position: absolute;
  top: 0;
  left: calc(100% + 6px);
  min-width: 180px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.has-sub:hover > .cm-submenu {
  display: block;
}
</style>
