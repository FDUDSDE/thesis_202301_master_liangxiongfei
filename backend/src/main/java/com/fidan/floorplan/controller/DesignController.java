package com.fidan.floorplan.controller;

import com.alibaba.fastjson.JSONObject;
import com.fidan.floorplan.service.RequestService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DesignController {

    @Autowired
    private RequestService requestService;
    @PostMapping("/algorithm/design")
    public JSONObject design(@RequestBody JSONObject designData) {
        JSONObject res = new JSONObject();
        JSONObject result = JSONObject.parseObject(requestService.post("https://localhost:5000/algorithm/design", designData.toJSONString()));
        return result;
    }
}
