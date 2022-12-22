<template>
  <div id="liang-home">
    <div class="home-title">
      <div class="btn-group">
        <a-button :type="selectedIndex === 0 ? 'primary' : 'info'" size="large" @click="changeSelectedIndex(0)">Predefined layouts 1</a-button>
        <a-button :type="selectedIndex === 1 ? 'primary' : 'info'" size="large" @click="changeSelectedIndex(1)">Predefined layouts 2</a-button>
        <a-button :type="selectedIndex === 2 ? 'primary' : 'info'" size="large" @click="changeSelectedIndex(2)">Predefined layouts 3</a-button>
        <a-button type="primary" size="large" :loading="loading" @click="generation" style="background-color: #22bb22; border: 1px solid #22bb22">生成</a-button>
<!--        <a-button :type="selectedIndex === 1 ? 'primary' : 'info'" size="large" @click="selectedIndex = 1">1-Bedroom Suite</a-button>-->
<!--        <a-button :type="selectedIndex === 2 ? 'primary' : 'info'" size="large" @click="selectedIndex = 2">2-Bedroom Suite</a-button>-->
<!--        <a-button :type="selectedIndex === 3 ? 'primary' : 'info'" size="large" @click="selectedIndex = 3">3-Bedroom Suite</a-button>-->
      </div>
      <div class="title-class">
        <span style="margin-right: 50px">
          <a-popover placement="bottom">
            <template slot="content">
              <div style="width: 100px">
                <a-button type="dash" block style="border: 0" @click="$router.replace('/account')">个人中心</a-button>
              </div>
            </template>
            <a-avatar :size="50" style="background-color: #7265e6">
              admin
            </a-avatar>
          </a-popover>
        </span>
<!--        <span>毕设系统</span>-->
      </div>
    </div>
    <div class="home-content">
      <div class="bubble-graph">
        <div class="bubble-graph-title">
          <a-col :span="4" v-for="(item, index) in rooms" :key="index">
            <a-card>
              <span slot="title" style="width: 100%; display: flex; justify-content: center">
                {{item.title}}
              </span>
              <a-popover placement="bottom">
                <template slot="title">
                  <span :style="{
                    color: item.backgroundColor,
                    fontSize: '20px',
                    fontWeight: 600
                  }">{{item.title}}</span>
                </template>
                <template slot="content">
                  <div style="width: 100%; display: flex; justify-content: center">
                    <a-button
                        type="primary"
                        shape="round"
                        :style="{
                          backgroundColor: item.backgroundColor,
                          border: `2px solid ${item.backgroundColor}`
                        }"
                        @click="appendBubbleNode(item)"
                    >
                      添加
                    </a-button>
                  </div>
                </template>
                <div style="height: 94px; width: 100%; display: flex; justify-content: center">
                  <div style="width: 80px; height: 80px; display: flex; justify-content: center" :style="{backgroundColor: item.backgroundColor}" />
                </div>
              </a-popover>
            </a-card>
          </a-col>
          <a-col :span="4">
            <div style="width: 100%; height: calc(60vh); background-color: white"></div>
          </a-col>
        </div>
        <div id="container"></div>
<!--        <div class="bubble-graph-content">-->
<!--          <div id="ball1"></div>-->
<!--          <div id="ball2"></div>-->
<!--          <div id="ball3"></div>-->
<!--          <div id="ball4"></div>-->
<!--          <div id="ball5"></div>-->
<!--        </div>-->
      </div>
      <a-divider type="vertical" style="height: calc(88vh); background-color: grey; border: 2px solid #d9d7d7" />
      <div class="result">
        <div class="result-show">
          <img v-if="nowResult" :src="nowResult.image" alt="" width="500px" />
          <div class="result-star">
            <a-icon v-if="nowResult" type="star" :theme="nowResult.isStar ? 'filled' : 'outlined'" :style="{
              color: nowResult.isStar ? '#ffd274' : 'black'
            }" @click="starResult" />
          </div>
        </div>
        <a-divider type="vertical" style="height: 98%; border: 2px solid grey; margin: 10px 10px" />
        <div class="all-result">
          <a-list item-layout="vertical" :data-source="showResults">
            <a-list-item slot="renderItem" :key="item.key" slot-scope="item, index">
              <a-card :title="`户型设计${index + 1}`" class="result-card" @click="nowResult = item">
                <img :src="item.image" alt="" width="60%" />
              </a-card>
            </a-list-item>
          </a-list>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import layout1res1 from '@/assets/img/results/layout1/output1.png'
import layout1res2 from '@/assets/img/results/layout1/output2.png'
import layout1res3 from '@/assets/img/results/layout1/output3.png'
import layout1res4 from '@/assets/img/results/layout1/output4.png'
import layout1res5 from '@/assets/img/results/layout1/output5.png'

import layout2res1 from '@/assets/img/results/layout2/output1.png'
import layout2res2 from '@/assets/img/results/layout2/output2.png'
import layout2res3 from '@/assets/img/results/layout2/output3.png'
import layout2res4 from '@/assets/img/results/layout2/output4.png'
import layout2res5 from '@/assets/img/results/layout2/output5.png'

import layout3res1 from '@/assets/img/results/layout3/output1.png'
import layout3res2 from '@/assets/img/results/layout3/output2.png'
import layout3res3 from '@/assets/img/results/layout3/output3.png'
import layout3res4 from '@/assets/img/results/layout3/output4.png'
import layout3res5 from '@/assets/img/results/layout3/output5.png'
import { Graph } from '@antv/x6';

import {STARRESULT, UNSTARRESULT} from "@/store/mutations-types";
// import { Edge } from '@antv/x6'
//
// class MyEdge extends Edge {}
// MyEdge.config({
//   attrs: {
//     line: {
//       sourceMarker: 'ellipse',
//       targetMarker: 'ellipse'
//     }
//   }
// })
// Graph.registerEdge('myEdge', MyEdge)

export default {
  name: "LiangHome",
  data() {
    return {
      loading: false,
      selectedIndex: 0,
      nodesCount: 100,
      rooms: [
        { title: '客厅', backgroundColor: '#ee4d4d' },
        { title: '厨房', backgroundColor: '#c67c7b' },
        { title: '卧室', backgroundColor: '#ffd274' },
        { title: '浴室', backgroundColor: '#bebebe' },
        { title: '阳台', backgroundColor: '#bfe3e8' },
        // { title: '餐厅', backgroundColor: '#e87a90' },
        // { title: '书房', backgroundColor: '#ff8c69' },
        // { title: '储藏室', backgroundColor: '#1f849b' },
      ],
      nodes: [
        {
          id: 'node1', // String，可选，节点的唯一标识
          x: 200,       // Number，必选，节点位置的 x 值
          y: 150,       // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'hello', // String，节点标签,
          shape: 'circle',
          attrs: {
            body: {
              fill: '#bebebe'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
        {
          id: 'node2', // String，节点的唯一标识
          x: 400,      // Number，必选，节点位置的 x 值
          y: 350,      // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'world', // String，节点标签
          shape: 'circle',
          attrs: {
            body: {
              fill: '#ee4d4d'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
        {
          id: 'node3', // String，节点的唯一标识
          x: 100,      // Number，必选，节点位置的 x 值
          y: 350,      // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'world', // String，节点标签
          shape: 'circle',
          attrs: {
            body: {
              fill: '#c67c7b'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
        {
          id: 'node4', // String，节点的唯一标识
          x: 200,      // Number，必选，节点位置的 x 值
          y: 550,      // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'world', // String，节点标签
          shape: 'circle',
          attrs: {
            body: {
              fill: '#bfe3e8'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
        {
          id: 'node5', // String，节点的唯一标识
          x: 600,      // Number，必选，节点位置的 x 值
          y: 150,      // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'world', // String，节点标签
          shape: 'circle',
          attrs: {
            body: {
              fill: '#ffd274'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
        {
          id: 'node6', // String，节点的唯一标识
          x: 600,      // Number，必选，节点位置的 x 值
          y: 550,      // Number，必选，节点位置的 y 值
          width: 100,   // Number，可选，节点大小的 width 值
          height: 100,  // Number，可选，节点大小的 height 值
          // label: 'world', // String，节点标签
          shape: 'circle',
          attrs: {
            body: {
              fill: '#ffd274'
            }
          },
          ports: {
            groups: {
              a: {
                position: {
                  name: 'ellipseSpread',
                  args: {
                    compensateRotate: true,
                  },
                },
                label: {
                  position: {
                    name: 'radial',
                  },
                },
                attrs: {
                  circle: {
                    fill: '#ffffff',
                    stroke: '#31d0c6',
                    strokeWidth: 2,
                    r: 4,
                    magnet: true,
                  },
                  text: {
                    fill: '#6a6c8a',
                    fontSize: 12,
                  },
                },
              },
            },
            items: [
              { id: 'port1', group: 'a' },
              { id: 'port2', group: 'a' },
              { id: 'port3', group: 'a' },
              { id: 'port4', group: 'a' }
            ]
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 85, y: 15 }, // 工具对应的参数
          // }
        },
      ],
      // 边
      edges: [
        {
          id: '1_2',
          source: 'node1', // String，必须，起始节点 id
          target: 'node2', // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        },
        {
          id: '2_3',
          source: 'node2', // String，必须，起始节点 id
          target: 'node3', // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        },
        {
          id: '2_4',
          source: 'node2', // String，必须，起始节点 id
          target: 'node4', // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        },
        {
          id: '2_5',
          source: 'node2', // String，必须，起始节点 id
          target: 'node5', // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        },
        {
          id: '2_6',
          source: 'node2', // String，必须，起始节点 id
          target: 'node6', // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        },
      ],
      graph: null,
      results: [
        { id: 1, image: layout1res1, isStar: false },
        { id: 2, image: layout1res2, isStar: false },
        { id: 3, image: layout1res3, isStar: false },
        { id: 4, image: layout1res4, isStar: false },
        { id: 5, image: layout1res5, isStar: false },
        { id: 6, image: layout2res1, isStar: false },
        { id: 7, image: layout2res2, isStar: false },
        { id: 8, image: layout2res3, isStar: false },
        { id: 9, image: layout2res4, isStar: false },
        { id: 10, image: layout2res5, isStar: false },
        { id: 11, image: layout3res1, isStar: false },
        { id: 12, image: layout3res2, isStar: false },
        { id: 13, image: layout3res3, isStar: false },
        { id: 14, image: layout3res4, isStar: false },
        { id: 15, image: layout3res5, isStar: false },
      ],
      clickIndex1: 0,
      clickIndex2: 5,
      clickIndex3: 10,
      showResults: [],
      nowResult: null
    }
  },
  methods: {
    appendBubbleNode(item) {
      console.log(item)
      this.nodesCount++
      this.nodes.push({
        id: 'node' + this.nodesCount, // String，节点的唯一标识
        x: Math.random()*1024,      // Number，必选，节点位置的 x 值
        y: Math.random()*736,      // Number，必选，节点位置的 y 值
        width: 100,   // Number，可选，节点大小的 width 值
        height: 100,  // Number，可选，节点大小的 height 值
        // label: 'world', // String，节点标签
        shape: 'circle',
        attrs: {
          body: {
            fill: item.backgroundColor
          }
        },
        ports: {
          groups: {
            a: {
              position: {
                name: 'ellipseSpread',
                args: {
                  compensateRotate: true,
                },
              },
              label: {
                position: {
                  name: 'radial',
                },
              },
              attrs: {
                circle: {
                  fill: '#ffffff',
                  stroke: '#31d0c6',
                  strokeWidth: 2,
                  r: 4,
                  magnet: true,
                },
                text: {
                  fill: '#6a6c8a',
                  fontSize: 12,
                },
              },
            },
          },
          items: [
            { id: 'port1', group: 'a' },
            { id: 'port2', group: 'a' },
            { id: 'port3', group: 'a' },
            { id: 'port4', group: 'a' }
          ]
        },
        // tools: {
        //   name: 'button-remove',  // 工具名称
        //   args: { x: 85, y: 15 }, // 工具对应的参数
        // }
      })
      // this.graph.on('node:mouseenter', ({ node }) => {
      //     node.addTools({
      //       name: 'button-remove',  // 工具名称
      //       args: { x: 85, y: 15 }, // 工具对应的参数
      //     })
      // })
      // this.graph.on('node:mouseleave', ({ node }) => {
      //   node.removeTools()
      // })
      this.graph.fromJSON({
        nodes: this.nodes,
        edges: this.edges
      })
    },
    generation() {
      this.loading = true
      setTimeout(() => {
        if(this.selectedIndex === 0) {
          this.showResults.push(this.results[this.clickIndex1])
          this.nowResult = this.results[this.clickIndex1]
          this.clickIndex1 = (this.clickIndex1 + 1) % 5
        } else if(this.selectedIndex === 1) {
          this.showResults.push(this.results[this.clickIndex2])
          this.nowResult = this.results[this.clickIndex2]
          this.clickIndex2 = (this.clickIndex2 + 1) % 10 + 5
        } else {
          this.showResults.push(this.results[this.clickIndex3])
          this.nowResult = this.results[this.clickIndex3]
          this.clickIndex3 = (this.clickIndex3 + 1) % 10 + 10
        }
        this.loading = false
      }, 3000)
    },
    starResult() {
      if(this.nowResult.isStar) {
        this.$store.commit(UNSTARRESULT, this.nowResult)
      } else {
        this.$store.commit(STARRESULT, this.nowResult)
      }
      this.nowResult.isStar = !this.nowResult.isStar
    },
    changeSelectedIndex(index) {
      this.selectedIndex = index
      if(index === 0) {
        this.nodes = [
          {
            id: 'node1', // String，可选，节点的唯一标识
            x: 200,       // Number，必选，节点位置的 x 值
            y: 150,       // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'hello', // String，节点标签,
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bebebe'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node2', // String，节点的唯一标识
            x: 400,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ee4d4d'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node3', // String，节点的唯一标识
            x: 100,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#c67c7b'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node4', // String，节点的唯一标识
            x: 200,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bfe3e8'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node5', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 150,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node6', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
        ]
        this.edges = [
          {
            id: '1_2',
            source: 'node1', // String，必须，起始节点 id
            target: 'node2', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_3',
            source: 'node2', // String，必须，起始节点 id
            target: 'node3', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_4',
            source: 'node2', // String，必须，起始节点 id
            target: 'node4', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_5',
            source: 'node2', // String，必须，起始节点 id
            target: 'node5', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_6',
            source: 'node2', // String，必须，起始节点 id
            target: 'node6', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
        ]
      } else if(index === 1) {
        this.nodes = [
          {
            id: 'node1', // String，可选，节点的唯一标识
            x: 200,       // Number，必选，节点位置的 x 值
            y: 150,       // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'hello', // String，节点标签,
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bebebe'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node2', // String，节点的唯一标识
            x: 400,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ee4d4d'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node3', // String，节点的唯一标识
            x: 100,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#c67c7b'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node4', // String，节点的唯一标识
            x: 200,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bfe3e8'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node5', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 150,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node6', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node7', // String，节点的唯一标识
            x: 750,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
        ]
        this.edges = [
          {
            id: '1_2',
            source: 'node1', // String，必须，起始节点 id
            target: 'node2', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_3',
            source: 'node2', // String，必须，起始节点 id
            target: 'node3', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_4',
            source: 'node2', // String，必须，起始节点 id
            target: 'node4', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_5',
            source: 'node2', // String，必须，起始节点 id
            target: 'node5', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_6',
            source: 'node2', // String，必须，起始节点 id
            target: 'node6', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_7',
            source: 'node2', // String，必须，起始节点 id
            target: 'node7', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
        ]
      } else {
        this.nodes = [
          {
            id: 'node1', // String，可选，节点的唯一标识
            x: 200,       // Number，必选，节点位置的 x 值
            y: 150,       // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'hello', // String，节点标签,
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bebebe'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node2', // String，节点的唯一标识
            x: 400,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ee4d4d'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node3', // String，节点的唯一标识
            x: 100,      // Number，必选，节点位置的 x 值
            y: 350,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#c67c7b'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node4', // String，节点的唯一标识
            x: 200,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#bfe3e8'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node5', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 150,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
          {
            id: 'node6', // String，节点的唯一标识
            x: 600,      // Number，必选，节点位置的 x 值
            y: 550,      // Number，必选，节点位置的 y 值
            width: 100,   // Number，可选，节点大小的 width 值
            height: 100,  // Number，可选，节点大小的 height 值
            // label: 'world', // String，节点标签
            shape: 'circle',
            attrs: {
              body: {
                fill: '#ffd274'
              }
            },
            ports: {
              groups: {
                a: {
                  position: {
                    name: 'ellipseSpread',
                    args: {
                      compensateRotate: true,
                    },
                  },
                  label: {
                    position: {
                      name: 'radial',
                    },
                  },
                  attrs: {
                    circle: {
                      fill: '#ffffff',
                      stroke: '#31d0c6',
                      strokeWidth: 2,
                      r: 4,
                      magnet: true,
                    },
                    text: {
                      fill: '#6a6c8a',
                      fontSize: 12,
                    },
                  },
                },
              },
              items: [
                { id: 'port1', group: 'a' },
                { id: 'port2', group: 'a' },
                { id: 'port3', group: 'a' },
                { id: 'port4', group: 'a' }
              ]
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 85, y: 15 }, // 工具对应的参数
            // }
          },
        ]
        this.edges = [
          {
            id: '1_2',
            source: 'node1', // String，必须，起始节点 id
            target: 'node2', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_3',
            source: 'node2', // String，必须，起始节点 id
            target: 'node3', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '6_4',
            source: 'node6', // String，必须，起始节点 id
            target: 'node4', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_5',
            source: 'node2', // String，必须，起始节点 id
            target: 'node5', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
          {
            id: '2_6',
            source: 'node2', // String，必须，起始节点 id
            target: 'node6', // String，必须，目标节点 id,
            attrs: {
              line: {
                sourceMarker: null,
                targetMarker: null
              }
            },
            // tools: {
            //   name: 'button-remove',  // 工具名称
            //   args: { x: 300, y: 0 }, // 工具对应的参数
            // }
          },
        ]
      }
      this.graph.fromJSON({
        nodes: this.nodes,
        edges: this.edges
      })
    }
  },
  mounted() {

    this.graph = new Graph({
      container: document.getElementById('container'),
      width: 1024,
      height: 736,
      background: {
        color: '#fffbe6', // 设置画布背景颜色
      },
    })
    this.graph.on('node:mouseenter', ({ node }) => {
      node.addTools({
        name: 'button-remove',  // 工具名称
        args: { x: 85, y: 15 }, // 工具对应的参数
      })
    })
    this.graph.on('node:mouseleave', ({ node }) => {
      node.removeTools()
    })
    this.graph.on('edge:mouseenter', ({ edge }) => {
      edge.addTools({
        name: 'button-remove',  // 工具名称
        // args: { x: 300, y: 0 }, // 工具对应的参数
      })
    })
    this.graph.on('edge:mouseleave', ({ edge }) => {
      edge.removeTools()
    })
    this.graph.on('edge:connected', ({ isNew, edge }) => {
      if (isNew) {
        // 对新创建的边进行插入数据库等持久化操作
        console.log(edge.source.cell.substring(4,), edge.target.cell.substring(4,))
        this.edges.push({
          id: edge.source.cell.substring(4,) + '_' + edge.target.cell.substring(4,),
          source: edge.source,
          target: edge.target, // String，必须，目标节点 id,
          attrs: {
            line: {
              sourceMarker: null,
              targetMarker: null
            }
          },
          // tools: {
          //   name: 'button-remove',  // 工具名称
          //   args: { x: 300, y: 0 }, // 工具对应的参数
          // }
        })
        this.graph.fromJSON({
          nodes: this.nodes,
          edges: this.edges
        })
        // this.edges.push(edge)
      }
    })
    this.graph.on('node:moved', ({ x, y, node }) => {
      console.log(x, y, node)
      let movedNode = this.nodes.find(item => item.id === node.id)
      movedNode.x = x - 50
      movedNode.y = y - 50
      // this.nodes[this.nodes.length - 1].x = (x - 20)
      // this.nodes[this.nodes.length - 1].y = (y - 40)
      // this.graph.fromJSON({
      //   nodes: this.nodes,
      //   edges: this.edges
      // })
    })
    this.graph.on('cell:removed', ({ cell, index, options }) => {
      console.log(cell, index, options)
      let ids = cell.id.split('_')
      if(ids.length === 1) {
        const delIndex = this.nodes.findIndex(node => node.id === ids[0])
        this.nodes.splice(delIndex, 1)
      } else {
        const delIndex = this.edges.findIndex(edge => edge.id === cell.id)
        this.edges.splice(delIndex, 1)
      }
    })
    this.graph.fromJSON({
      nodes: this.nodes,
      edges: this.edges
    })
  }
}
</script>

<style scoped>
#liang-home {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  width: calc(100vw);
  height: calc(100vh);
}
.home-title {
  width: 100%;
  padding: 5px 20px 5px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.btn-group {
  width: 40%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title-class {
  font-size: 30px;
}
.home-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(90vh);
}
.bubble-graph {
  width: calc(48vw);
  height: 100%;
  background-color: #d9d7d7;
  margin: 5px;
  /*position: relative;*/
}
.result {
  width: calc(48vw);
  height: 100%;
  /*background-color: #d9d7d7;*/
  margin: 5px;
  display: flex;
  flex-direction: row;
}
.bubble-graph div:nth-child(n+1) {
  border-radius: 50px;
}
#container {
  position: absolute;
  top: 263px;
  left: 28px;
}
#ball1 {
  width: 100px;
  height: 100px;
  background-color: #ee4d4d;
  /*border-radius: 24px;*/
  position: absolute;
  top: 600px;
  left: 500px;
}
#ball2 {
  width: 100px;
  height: 100px;
  background-color: #ffd274;
  /*border-radius: 24px;*/
  position: absolute;
  top: 400px;
  left: 700px;
}
#ball3 {
  width: 100px;
  height: 100px;
  background-color: #bebebe;
  /*border-radius: 24px;*/
  position: absolute;
  top: 400px;
  left: 300px;
}
#ball4 {
  width: 100px;
  height: 100px;
  background-color: #c67c7b;
  /*border-radius: 24px;*/
  position: absolute;
  top: 600px;
  left: 300px;
}
#ball5 {
  width: 100px;
  height: 100px;
  background-color: #bfe3e8;
  /*border-radius: 24px;*/
  position: absolute;
  top: 800px;
  left: 300px;
}
.bubble-graph-title >>> * {
  /*background-color: red;*/
  border-radius: 0 !important;
}
.result-show {
  width: 80%;
  height: 100%;
  background-color: white !important;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}
.all-result {
  width: 18%;
  height: 1000px;
  display: flex;
  justify-content: center;
  /*background-color: blue;*/
}
.result-card {
  width: 180px;
  border-radius: 24px;
}
.result-card >>> .ant-card-body {
  display: flex;
  justify-content: center;
  align-items: center;
}
.result-card:hover {
  background-color: #bfe3e8;
  cursor: pointer;
}
.result-star {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 30px;
  transition: .3s;
}
.result-star:hover {
  font-size: 35px;
  cursor: pointer;
}
</style>
