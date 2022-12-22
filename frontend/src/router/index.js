import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const LiangHome = () => import('@/views/LiangHome')
const LiangLogin = () => import('@/views/LiangLogin')
const LiangAccount = () => import('@/views/LiangAccount')

const routes = [
  {
    path: '',
    redirect: '/login'
  },
  {
    path: '/login',
    component: LiangLogin
  },
  {
    path: '/home',
    component: LiangHome
  },
  {
    path: '/account',
    component: LiangAccount
  }
]

const router = new VueRouter({
  routes,
  mode: 'history'
})

export default router
