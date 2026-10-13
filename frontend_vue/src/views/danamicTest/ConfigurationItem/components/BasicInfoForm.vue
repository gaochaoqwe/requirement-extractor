<template>
  <div class="basic-info-form">
    <el-form :model="basicInfo" :rules="basicInfoRules" ref="basicInfoForm" label-width="120px">
      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="所属领域" prop="domain">
            <el-select 
              v-model="basicInfo.domain" 
              placeholder="请选择所属领域" 
              style="width: 100%" 
              filterable
              allow-create
              default-first-option
              @change="handleDomainChange"
            >
              <el-option
                v-for="domain in domains"
                :key="domain.value"
                :label="domain.label"
                :value="domain.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="测试主管" prop="testManager">
            <el-select 
              v-model="basicInfo.testManager" 
              placeholder="请选择测试主管" 
              style="width: 100%" 
              filterable
              allow-create
              default-first-option
              @change="handleTestManagerChange"
            >
              <el-option
                v-for="manager in testManagers"
                :key="manager.value"
                :label="manager.label"
                :value="manager.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="测试人员" prop="testPersonnel">
            <el-select 
              v-model="basicInfo.testPersonnel" 
              placeholder="请选择测试人员" 
              style="width: 100%" 
              filterable
              allow-create
              default-first-option
              @change="handleTestPersonnelChange"
            >
              <el-option
                v-for="personnel in testPersonnels"
                :key="personnel.value"
                :label="personnel.label"
                :value="personnel.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="开发人员" prop="developer">
            <el-select 
              v-model="basicInfo.developer" 
              placeholder="请选择开发人员" 
              style="width: 100%" 
              filterable
              allow-create
              default-first-option
              @change="handleDeveloperChange"
            >
              <el-option
                v-for="dev in developers"
                :key="dev.value"
                :label="dev.label"
                :value="dev.value">
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="软件名称" prop="softwareName">
            <el-input v-model="basicInfo.softwareName" placeholder="请输入软件名称"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="软件版本" prop="softwareVersion">
            <el-input v-model="basicInfo.softwareVersion" placeholder="请输入软件版本"></el-input>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="24">
        <el-col :span="12">
          <el-form-item label="软件ID" prop="softwareId">
            <el-input v-model="basicInfo.softwareId" placeholder="请输入软件ID"></el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="组件" prop="productType">
            <el-select 
              v-model="basicInfo.productType" 
              placeholder="请选择组件" 
              style="width: 100%"
              @change="handleProductTypeChange"
            >
              <el-option label="转塔" value="转塔"></el-option>
              <el-option label="对抗告警" value="对抗告警"></el-option>
              <el-option label="光电雷达" value="光电雷达"></el-option>
              <el-option label="吊舱" value="吊舱"></el-option>
              <el-option label="火控" value="火控"></el-option>
              <el-option label="外挂" value="外挂"></el-option>
              <el-option label="显示" value="显示"></el-option>
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
          <el-form-item label="AI分析">
            <el-switch v-model="basicInfo.aiAnalysis" active-text="启用" inactive-text="禁用"></el-switch>
            <el-switch v-model="basicInfo.deepAnalysis" active-text="深度分析" inactive-text="常规分析" style="margin-left: 10px"></el-switch>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'BasicInfoForm',
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
        domain: '',
        testManager: '',
        testPersonnel: '',
        developer: '',
        softwareName: '',
        softwareVersion: '',
        softwareId: '',
        productType: '',
        detectorFlag: '有检测仪',
        aiAnalysis: true,
        deepAnalysis: false
      },
      basicInfoRules: {
        domain: [
          { required: true, message: '请选择所属领域', trigger: 'change' }
        ],
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
        softwareId: [
          { required: true, message: '请输入软件ID', trigger: 'blur' }
        ],
        productType: [
          { required: true, message: '请选择组件', trigger: 'change' }
        ]
      },
      domains: [],
      testManagers: [],
      testPersonnels: [],
      developers: []
    }
  },
  async mounted() {
    await this.loadDropdownData()
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
        console.log('子组件 basicInfo 变化:', newVal);
        this.$emit('update:modelValue', { ...newVal });
      },
      deep: true
    }
  },
  methods: {
    async loadDropdownData() {
      try {
        // 并行加载所有下拉数据
        const [domainsRes, managersRes, personnelRes, developersRes] = await Promise.all([
          axios.get('/api/dynamic-test/configuration/dropdown-data/domains'),
          axios.get('/api/dynamic-test/configuration/dropdown-data/test-managers'),
          axios.get('/api/dynamic-test/configuration/dropdown-data/test-personnel'),
          axios.get('/api/dynamic-test/configuration/dropdown-data/developers')
        ])

        this.domains = domainsRes.data.data || []
        this.testManagers = managersRes.data.data || []
        this.testPersonnels = personnelRes.data.data || []
        this.developers = developersRes.data.data || []
      } catch (error) {
        console.error('加载下拉数据失败:', error)
        this.$message.error('加载下拉数据失败')
      }
    },
    
    async handleDomainChange(value) {
      // 如果选择的值不在现有选项中，说明是新输入的，需要添加到数据库
      if (value && !this.domains.find(item => item.value === value)) {
        try {
          const formData = new FormData()
          formData.append('name', value)
          
          await axios.post('/api/dynamic-test/configuration/dropdown-data/domains', formData)
          
          // 重新加载域数据
          const response = await axios.get('/api/dynamic-test/configuration/dropdown-data/domains')
          this.domains = response.data.data || []
          
          this.$message.success('新领域添加成功')
        } catch (error) {
          console.error('添加领域失败:', error)
          if (error.response?.status === 400) {
            this.$message.warning('该领域已存在')
          } else {
            this.$message.error('添加领域失败')
          }
        }
      }
    },
    
    async handleTestManagerChange(value) {
      if (value && !this.testManagers.find(item => item.value === value)) {
        try {
          const formData = new FormData()
          formData.append('name', value)
          
          await axios.post('/api/dynamic-test/configuration/dropdown-data/test-managers', formData)
          
          const response = await axios.get('/api/dynamic-test/configuration/dropdown-data/test-managers')
          this.testManagers = response.data.data || []
          
          this.$message.success('新测试主管添加成功')
        } catch (error) {
          console.error('添加测试主管失败:', error)
          if (error.response?.status === 400) {
            this.$message.warning('该测试主管已存在')
          } else {
            this.$message.error('添加测试主管失败')
          }
        }
      }
    },
    
    async handleTestPersonnelChange(value) {
      if (value && !this.testPersonnels.find(item => item.value === value)) {
        try {
          const formData = new FormData()
          formData.append('name', value)
          
          await axios.post('/api/dynamic-test/configuration/dropdown-data/test-personnel', formData)
          
          const response = await axios.get('/api/dynamic-test/configuration/dropdown-data/test-personnel')
          this.testPersonnels = response.data.data || []
          
          this.$message.success('新测试人员添加成功')
        } catch (error) {
          console.error('添加测试人员失败:', error)
          if (error.response?.status === 400) {
            this.$message.warning('该测试人员已存在')
          } else {
            this.$message.error('添加测试人员失败')
          }
        }
      }
    },
    
    async handleDeveloperChange(value) {
      if (value && !this.developers.find(item => item.value === value)) {
        try {
          const formData = new FormData()
          formData.append('name', value)
          
          await axios.post('/api/dynamic-test/configuration/dropdown-data/developers', formData)
          
          const response = await axios.get('/api/dynamic-test/configuration/dropdown-data/developers')
          this.developers = response.data.data || []
          
          this.$message.success('新开发人员添加成功')
        } catch (error) {
          console.error('添加开发人员失败:', error)
          if (error.response?.status === 400) {
            this.$message.warning('该开发人员已存在')
          } else {
            this.$message.error('添加开发人员失败')
          }
        }
      }
    },
    
    handleProductTypeChange(value) {
      console.log('组件类型变化:', value);
      // 组件类型变化时可以进行相关处理
      // 这个值会通过watch机制自动传递给父组件
    },
    
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
.basic-info-form {
  padding: 20px;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-switch {
  margin-right: 10px;
}
</style> 