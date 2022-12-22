import { request } from "@/network/request";

export function roomDesign(nodes_num, type, edges) {
  return request({
    url: '/algorithm/design',
    method: 'post',
    data: {
      nodes_num,
      type,
      edges,
    }
  })
}
