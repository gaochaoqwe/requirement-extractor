import { defineStore } from 'pinia';
import request from '@/api/request'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated
  },

  actions: {
    async login(username, password) {
      try {
        const data = await request.post(`/auth/login`, {
          username,
          password
        }, {
          withCredentials: true  // 支持cookie/session
        });

        if (data.success) {
          this.user = data.data.user;
          this.token = data.data.token;
          this.isAuthenticated = true;

          // 保存到localStorage
          localStorage.setItem('token', this.token);
          localStorage.setItem('user', JSON.stringify(this.user));

          return data;
        } else {
          throw new Error(data.message || '登录失败');
        }
      } catch (error) {
        console.error('登录失败:', error);
        throw error;
      }
    },

    async logout() {
      try {
        await request.post(`/auth/logout`, {}, {
          withCredentials: true
        });
      } catch (error) {
        console.error('登出请求失败:', error);
      } finally {
        // 清除状态
        this.user = null;
        this.token = null;
        this.isAuthenticated = false;

        // 清除localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    },

    async checkAuth() {
      try {
        const data = await request.get(`/auth/check`, {
          withCredentials: true,
          headers: this.token ? {
            'Authorization': `Bearer ${this.token}`
          } : {}
        });

        if (data.success && data.authenticated) {
          this.user = data.user;
          this.isAuthenticated = true;
          return true;
        } else {
          this.user = null;
          this.isAuthenticated = false;
          return false;
        }
      } catch (error) {
        console.error('检查登录状态失败:', error);
        this.user = null;
        this.isAuthenticated = false;
        return false;
      }
    },

    initFromStorage() {
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');

      if (token && userStr) {
        try {
          this.token = token;
          this.user = JSON.parse(userStr);
          this.isAuthenticated = true;
        } catch (error) {
          console.error('从localStorage恢复用户信息失败:', error);
          this.logout();
        }
      }
    }
  }
});
