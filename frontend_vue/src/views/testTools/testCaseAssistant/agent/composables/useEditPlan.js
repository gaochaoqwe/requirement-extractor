import { ref, computed } from 'vue'

export function useEditPlan() {
  const pendingPlans = ref([])
  const currentPlanIndex = ref(0)
  const appliedOps = ref([])

  const currentPlan = computed(() => pendingPlans.value[currentPlanIndex.value] || null)
  const hasPending = computed(() => pendingPlans.value.length > 0)
  const totalOps = computed(() => currentPlan.value?.operations?.length || 0)
  const currentOpIndex = ref(0)
  const currentOp = computed(() => currentPlan.value?.operations?.[currentOpIndex.value] || null)

  const addPlan = (plan) => {
    pendingPlans.value.push({ ...plan, _opIndex: 0 })
    if (pendingPlans.value.length === 1) {
      currentPlanIndex.value = 0
      currentOpIndex.value = 0
    }
  }

  const acceptCurrentOp = () => {
    const op = currentOp.value
    if (!op) return null
    appliedOps.value.push(op)
    currentOpIndex.value++
    if (currentOpIndex.value >= totalOps.value) {
      _advancePlan()
    }
    return op
  }

  const skipCurrentOp = () => {
    currentOpIndex.value++
    if (currentOpIndex.value >= totalOps.value) {
      _advancePlan()
    }
  }

  const acceptAll = () => {
    const plan = currentPlan.value
    if (!plan) return []
    const ops = plan.operations.slice(currentOpIndex.value)
    appliedOps.value.push(...ops)
    _advancePlan()
    return ops
  }

  const dismissPlan = () => { _advancePlan() }

  const _advancePlan = () => {
    pendingPlans.value.splice(currentPlanIndex.value, 1)
    currentOpIndex.value = 0
    if (currentPlanIndex.value >= pendingPlans.value.length) {
      currentPlanIndex.value = Math.max(0, pendingPlans.value.length - 1)
    }
  }

  const clear = () => {
    pendingPlans.value = []
    currentPlanIndex.value = 0
    currentOpIndex.value = 0
    appliedOps.value = []
  }

  return {
    pendingPlans, currentPlan, hasPending,
    totalOps, currentOpIndex, currentOp,
    addPlan, acceptCurrentOp, skipCurrentOp, acceptAll, dismissPlan, clear,
  }
}
