<template>
  <el-dialog
    v-model="visibleProxy"
    title="组织资产复用（选中行）"
    width="480px"
    :close-on-click-modal="false"
  >
    <div class="form">
      <div class="form-item">
        <label class="form-label">选择产品类型：</label>
        <el-select v-model="state.selectedType" placeholder="请选择产品类型" style="width: 100%">
          <el-option label="转塔" value="转塔" />
          <el-option label="对抗告警" value="对抗告警" />
          <el-option label="光雷" value="光雷" />
          <el-option label="吊舱" value="吊舱" />
        </el-select>
      </div>

      <div class="form-item" v-if="state.availableSoftwareTypes.length > 0">
        <label class="form-label">选择软件类型：</label>
        <el-select v-model="state.selectedSoftwareType" placeholder="请选择软件类型" style="width: 100%">
          <el-option
            v-for="softwareType in state.availableSoftwareTypes"
            :key="softwareType"
            :label="softwareType"
            :value="softwareType"
          />
        </el-select>
      </div>

      <div class="hint">
        将根据选中行的 O 列“测试项名称”，从组织资产库匹配并回填到 T/U 列。
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visibleProxy = false">取消</el-button>
        <el-button type="primary" @click="confirm" :disabled="!state.selectedType || !state.selectedSoftwareType">
          开始匹配
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  visible: { type: Boolean, default: false },
  taskId: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'confirm'])

const visibleProxy = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const state = reactive({
  selectedType: '',
  selectedSoftwareType: '',
  availableSoftwareTypes: [],
})

let hydrating = false

const productSoftwareMapping = {
  转塔: ['主控', '随动', '图像', '红外', '激光'],
  对抗告警: ['告警主控', '告警红外', '分色滤光', '目标检测', '拼接', '干扰主控', '伺服', '干扰红外', '干扰图像', '干扰激光'],
  光雷: ['主控', '随动', '红外', '图像', '激光'],
  吊舱: ['主控', '随动', '图像', '红外', '激光'],
}

watch(
  () => state.selectedType,
  (newType) => {
    if (!hydrating) state.selectedSoftwareType = ''
    state.availableSoftwareTypes = newType && productSoftwareMapping[newType] ? productSoftwareMapping[newType] : []
  }
)

watch(
  () => props.visible,
  (v) => {
    if (v) {
      reset()
      hydrateFromTask()
    }
  }
)

async function hydrateFromTask() {
  const tid = props.taskId
  if (!tid) return
  try {
    hydrating = true
    const resp = await request.get(`/test-tools/test-case-assistant/tasks/${tid}`)
    const productType = resp?.product_type
    const softwareType = resp?.software_type

    if (productType) {
      state.selectedType = productType
      state.availableSoftwareTypes = productSoftwareMapping[productType] ? productSoftwareMapping[productType] : []
    }
    if (softwareType) state.selectedSoftwareType = softwareType
  } catch (_) {
    // ignore
  } finally {
    hydrating = false
  }
}

function reset() {
  state.selectedType = ''
  state.selectedSoftwareType = ''
  state.availableSoftwareTypes = []
}

function confirm() {
  emit('confirm', {
    selectedType: state.selectedType,
    selectedSoftwareType: state.selectedSoftwareType,
  })
  visibleProxy.value = false
}
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  color: #374151;
}

.hint {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}
</style>
