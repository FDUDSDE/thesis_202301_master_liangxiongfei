import Vue from 'vue'
import Vuex from 'vuex'

import {STARRESULT, UNSTARRESULT} from "@/store/mutations-types";

Vue.use(Vuex)

const state = {
  starResults: []
}

const store = new Vuex.Store({
  state,
  mutations: {
    [STARRESULT](state, payload) {
      const index = state.starResults.findIndex(item => item.id === payload.id)
      if(index === -1) {
        state.starResults.push(payload)
      }
    },
    [UNSTARRESULT](state, payload) {
      const index = state.starResults.findIndex(item => item.id === payload.id)
      if(index !== -1) {
        state.starResults.splice(index, 1)
      }
    }
  },
  getters: {},
  actions: {},
  modules: {}
})

export default store
