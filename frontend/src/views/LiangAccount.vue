<template>
  <div id="account">
    <a-layout id="components-layout-demo-custom-trigger">
      <a-layout-sider v-model="collapsed" :trigger="null" collapsible style="height: calc(100vh)">
        <div class="logo" @click="$router.push('/home')" />
        <a-menu v-model="openKey" theme="light" mode="inline" :default-selected-keys="['1']">
          <a-menu-item key="1">
            <a-icon type="user" />
            <span>个人中心</span>
          </a-menu-item>
          <a-menu-item key="2">
            <a-icon type="video-camera" />
            <span>我的收藏</span>
          </a-menu-item>
<!--          <a-menu-item key="3">-->
<!--            <a-icon type="upload" />-->
<!--            <span>nav 3</span>-->
<!--          </a-menu-item>-->
        </a-menu>
      </a-layout-sider>
      <a-layout>
        <a-layout-header style="background: #fff; padding: 0">
          <a-icon
              class="trigger"
              :type="collapsed ? 'menu-unfold' : 'menu-fold'"
              @click="() => (collapsed = !collapsed)"
          />
        </a-layout-header>
        <a-layout-content
            :style="{ margin: '24px 16px', padding: '24px', background: '#fff', minHeight: '280px' }"
        >
          <div v-if="openKey[0] === '1'">
            <a-divider>用户信息</a-divider>
            <a-card title="用户信息" style="width: 100%">
              <a-card-meta>
                <a-avatar
                    slot="avatar"
                    :size="64"
                    style="background-color: #7265e6"
                    >
                  admin
                </a-avatar>
                <div slot="description">
                  <a-row :gutter="24">
                    <a-col :span="8">
                      <span>ID：178064109</span>
                    </a-col>
                    <a-col :span="8">
                      <span>用户名：Admin</span>
                    </a-col>
                    <a-col :span="8">
                      <span>密码：**********&nbsp;&nbsp;<a-icon type="edit" style="color: deepskyblue" /></span>
                    </a-col>
                  </a-row>
                </div>
                <span slot="title" style="font-size: 24px; font-weight: 600; color: #7265e6">Admin</span>
              </a-card-meta>
            </a-card>
          </div>
          <div v-else-if="openKey[0] === '2'">
            <a-divider>收藏户型</a-divider>
            <a-list :grid="{ gutter: 16, column: 4 }" :data-source="$store.state.starResults">
              <a-list-item slot="renderItem" slot-scope="item, index">
                <a-card :title="`收藏户型${index + 1}`" class="card-item">
                  <img :src="item.image" alt="" />
                </a-card>
              </a-list-item>
            </a-list>
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </div>
</template>

<script>
import userIcon from '@/assets/img/user/userIcon.jpg'
export default {
  name: "LiangAccount",
  data() {
    return {
      collapsed: false,
      openKey: ['1'],
      userIcon: userIcon
    };
  }
}
</script>

<style scoped>
#components-layout-demo-custom-trigger .trigger {
  font-size: 18px;
  line-height: 64px;
  padding: 0 24px;
  cursor: pointer;
  transition: color 0.3s;
}

#components-layout-demo-custom-trigger .trigger:hover {
  color: #1890ff;
}

#components-layout-demo-custom-trigger .logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  margin: 16px;
  cursor: pointer;
  transition: 0.5s;
}
#components-layout-demo-custom-trigger .logo:hover {
  background: rgba(255, 255, 255, 0.5);
}
.card-item {
  border-radius: 24px;
  height: 300px;
}
.card-item >>> .ant-card-body {
  display: flex;
  justify-content: center;
  align-items: center;
}
.ant-layout-sider {
  background-color: #5aa04d;
}
</style>
