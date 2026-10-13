<template>
  <div class="regression-basic-info">
    <el-form :model="basicInfo" :rules="basicInfoRules" ref="basicInfoForm" label-width="120px">
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="测试主管" prop="testManager">
            <el-select v-model="basicInfo.testManager" placeholder="请选择测试主管" style="width: 100%">
              <el-option
                v-for="manager in testManagers"
                :key="manager.value"
                :label="manager.label"
                :value="manager.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="测试人员" prop="testPersonnel">
            <el-select v-model="basicInfo.testPersonnel" placeholder="请选择测试人员" style="width: 100%">
              <el-option
                v-for="personnel in testPersonnels"
                :key="personnel.value"
                :label="personnel.label"
                :value="personnel.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="开发人员" prop="developer">
            <el-select v-model="basicInfo.developer" placeholder="请选择开发人员" style="width: 100%">
              <el-option
                v-for="dev in developers"
                :key="dev.value"
                :label="dev.label"
                :value="dev.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="软件名称" prop="softwareName">
            <el-input v-model="basicInfo.softwareName" placeholder="请输入软件名称"></el-input>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="软件版本" prop="softwareVersion">
            <el-input v-model="basicInfo.softwareVersion" placeholder="请输入软件版本"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="所属领域" prop="domain">
            <el-select v-model="basicInfo.domain" placeholder="请选择所属领域" style="width: 100%">
              <el-option
                v-for="domain in domains"
                :key="domain.value"
                :label="domain.label"
                :value="domain.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="检测仪配置">
            <el-radio-group v-model="basicInfo.detectorFlag">
              <el-radio value="有检测仪">有检测仪</el-radio>
              <el-radio value="无检测仪">无检测仪</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分析选项">
            <el-switch v-model="basicInfo.aiAnalysis" active-text="AI分析" inactive-text="常规分析"></el-switch>
            <el-switch v-model="basicInfo.deepAnalysis" active-text="深度分析" inactive-text="浅度分析" style="margin-left: 10px"></el-switch>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="24">
          <el-form-item label="回归测试范围">
            <el-checkbox-group v-model="basicInfo.testScope">
              <el-checkbox value="功能回归">功能回归测试</el-checkbox>
              <el-checkbox value="性能回归">性能回归测试</el-checkbox>
              <el-checkbox value="接口回归">接口回归测试</el-checkbox>
              <el-checkbox value="安全回归">安全回归测试</el-checkbox>
              <el-checkbox value="兼容性回归">兼容性回归测试</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script>
export default {
  name: 'RegressionBasicInfo',
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'validate'],
  data() {
    return {
      basicInfo: {
        testManager: '',
        testPersonnel: '',
        developer: '',
        softwareName: '',
        softwareVersion: '',
        domain: '',
        detectorFlag: '有检测仪',
        aiAnalysis: true,
        deepAnalysis: false,
        testScope: ['功能回归']
      },
      basicInfoRules: {
        testManager: [
          { required: true, message: '请选择测试主管', trigger: 'change' }
        ],
        testPersonnel: [
          { required: true, message: '请选择测试人员', trigger: 'change' }
        ],
        developer: [
          { required: true, message: '请选择开发人员', trigger: 'change' }
        ],
        softwareName: [
          { required: true, message: '请输入软件名称', trigger: 'blur' }
        ],
        softwareVersion: [
          { required: true, message: '请输入软件版本', trigger: 'blur' }
        ],
        domain: [
          { required: true, message: '请选择所属领域', trigger: 'change' }
        ]
      },
      testManagers: [
        { value: '张三', label: '张三' },
        { value: '李四', label: '李四' },
        { value: '王五', label: '王五' }
      ],
      testPersonnels: [
        { value: '测试员A', label: '测试员A' },
        { value: '测试员B', label: '测试员B' },
        { value: '测试员C', label: '测试员C' }
      ],
      developers: [
        { value: '开发者A', label: '开发者A' },
        { value: '开发者B', label: '开发者B' },
        { value: '开发者C', label: '开发者C' }
      ],
      domains: [
        { value: '通用软件', label: '通用软件' },
        { value: '嵌入式软件', label: '嵌入式软件' },
        { value: 'Web应用', label: 'Web应用' },
        { value: '移动应用', label: '移动应用' },
        { value: '系统软件', label: '系统软件' }
      ]
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        if (newVal) {
          this.basicInfo = { ...this.basicInfo, ...newVal };
        }
      },
      deep: true,
      immediate: true
    },
    basicInfo: {
      handler(newVal) {
        console.log('回归测试子组件 basicInfo 变化:', newVal);
        this.$emit('update:modelValue', { ...newVal });
      },
      deep: true
    }
  },
  methods: {
    validate() {
      return this.$refs.basicInfoForm.validate();
    },
    resetForm() {
      this.$refs.basicInfoForm.resetFields();
    }
  }
}
</script>

<style scoped>
.regression-basic-info {
  padding: 20px;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-switch {
  margin-right: 10px;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}
</style> 