<template>
  <div id="login" class="flex-row">
    <div class="left">
<!--      <div class="logo">-->
<!--        <img src="~@/assets/img/login/logo.png" alt="" />-->
<!--      </div>-->
      <div class="title">智能户型设计系统</div>
      <div class="Illustration">
        <img src="~@/assets/img/login/Illustration.png" />
      </div>
    </div>
    <div class="right">
      <div>
        <div style="font-size: 22px; color: #0A1629; margin-bottom: 51px; width: 543px; text-align: center">
          Sign In to AI-BUILDING
        </div>
        <a-form
            id="components-form-demo-normal-login"
            :form="form"
            class="login-form"
            @submit="handleSubmit"
        >
          <a-space direction="vertical" size="large">
            <a-row>
              <a-col :span="24">用户ID</a-col>
              <br/>
              <br/>
              <a-col :span="24">
                <a-form-item>
                  <a-input
                      v-decorator="[
                          'userName',
                          { rules: [{ required: true, message: 'Please input your username!' }] },
                      ]"
                      placeholder="请输入ID/手机号/邮箱地址"
                      size="large"
                  >
                  </a-input>
                </a-form-item>
              </a-col>
            </a-row>
            <a-row>
              <a-col :span="24">密码</a-col>
              <br/>
              <br/>
              <a-col :span="24">
                <a-form-item>
                  <a-input-password
                      v-decorator="[
                          'password',
                          { rules: [{ required: true, message: 'Please input your Password!' }] },
                      ]"
                      type="password"
                      placeholder="请输入密码"
                      size="large"
                  >
                  </a-input-password>
                </a-form-item>
              </a-col>
            </a-row>
            <a-row>
              <a-col :span="24">
                <a-form-item>
                  <a-checkbox
                      v-decorator="[
                          'remember',
                          {
                            valuePropName: 'checked',
                            initialValue: true,
                          },
                      ]"
                  >
                    记住密码
                  </a-checkbox>
                  <a class="login-form-forgot" href="">
                    忘记密码？
                  </a>
                  <div style="display: flex; justify-content: center; align-items: center; width: 543px; margin-top: 67px; margin-bottom: 27px">
                    <a-button type="primary" html-type="submit" class="login-form-button">
                      Sign in
                    </a-button>
                  </div>
                  <div style="display: flex; justify-content: center; align-items: center; width: 543px">
                    <a href="" class="register-link">
                      还没有账户？立即注册
                    </a>
                  </div>
                </a-form-item>
              </a-col>
            </a-row>
          </a-space>
        </a-form>
      </div>
    </div>
  </div>
</template>

<script>
import { login } from "@/network/user";

export default {
  name: "LiangLogin",
  data() {
    return {
      form: this.$form.createForm(this, { name: 'normal_login' })
    }
  },
  methods: {
    handleSubmit(e) {
      e.preventDefault()
      this.form.validateFields((err, values) => {
        if (!err) {
          console.log('Received values of form: ', values)
          login(values.userName, values.password).then(res => {
            if(res) {
              this.$router.replace('/home')
            }
          }, err => {
            console.log(err)
          })
          // this.$store.commit(SETUSER, {username: values.userName})
          this.$router.replace('/home')
        }
      })
    }
  }
}
</script>

<style scoped>
#login {
  width: 2000px;
  height: 1036px;
  padding: 22px;
}

#login .left {
  background-color: #5aa04d;
  width: 757px;
  height: 1036px;
  border-radius: 24px 0 0 24px;
}

#login .right {
  width: 1119px;
  height: 1036px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.flex-row {
  display: flex;
  flex-direction: row;
}

.logo {
  margin-left: 127px;
  padding-top: 80px;
}

.title {
  margin-top: 116px;
  margin-left: 127px;
  font-size: 40px;
  color: #fff;
}

.Illustration {
  margin-top: 126px;
  margin-left: 109px;
}

#components-form-demo-normal-login .login-form {
  max-width: 300px;
}
#components-form-demo-normal-login .login-form-forgot {
  float: right;
  color: #7D8592;
}
#components-form-demo-normal-login .login-form-button {
  width: 229px;
  background-color: #5aa04d;
  border: 1px solid #5aa04d;
}
.register-link {
  color: #5aa04d;
}
.register-link:hover {
  color: #44803a;
}
</style>
