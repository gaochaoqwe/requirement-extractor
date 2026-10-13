<template>
  <div class="document-review-container">
    <!-- 子路由内容直接渲染，不显示标题和二级导航 -->
    <router-view />
  </div>
</template>

<script setup>
// 这个组件只作为容器，没有特定的业务逻辑
</script>

<style scoped>
.document-review-container {
  width: 100%;
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 25px;
  font-size: 1.8rem;
  position: relative;
  padding-bottom: 10px;
}

h2::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 50px;
  height: 3px;
  background-color: #3498db;
  border-radius: 3px;
}

.sub-navigation {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.sub-nav-item {
  padding: 12px 20px;
  margin-right: 10px;
  text-decoration: none;
  color: #7f8c8d;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  font-weight: 500;
}

.sub-nav-item:hover {
  color: #3498db;
}

.sub-nav-item.active {
  color: #3498db;
  border-bottom: 3px solid #3498db;
  font-weight: 700;
}
</style>
