import axios from "axios"

export function request(config) {
  const instance = axios.create({
    baseURL: '/api',
    timeout: 5000
  })

  instance.interceptors.request.use(config => {
    // console.log(config.data);
    return config
  }, err => {
    console.log(err);
  })

  instance.interceptors.response.use(res => {
    // console.log(res.data);
    return res.data
  }, err => {
    console.log(err);
  })

  return instance(config)
}
