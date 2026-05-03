/**
 * 认证工具模块
 */

const TOKEN_KEY = 'tdx_token'
const USER_KEY = 'tdx_user'

/**
 * 获取 Token
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 设置 Token
 */
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 移除 Token
 */
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * 获取用户信息
 */
export function getUser() {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch (e) {
      return null
    }
  }
  return null
}

/**
 * 设置用户信息
 */
export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * 检查是否已登录
 */
export function isLoggedIn() {
  return !!getToken()
}

/**
 * 获取用户角色
 */
export function getUserRole() {
  const user = getUser()
  return user?.role || 'guest'
}

/**
 * 检查是否是管理员
 */
export function isAdmin() {
  return getUserRole() === 'admin'
}
