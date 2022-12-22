import { request } from "@/network/request";

export function login(username, password) {
  return request({
    url: '/login',
    method: 'post',
    data: {
      username,
      password
    }
  })
}

export function register(username, email, phone, password) {
  return request({
    url: '/register',
    method: 'post',
    data: {
      username,
      email,
      phone,
      password
    }
  })
}
