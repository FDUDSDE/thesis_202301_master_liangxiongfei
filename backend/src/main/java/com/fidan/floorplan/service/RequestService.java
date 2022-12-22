package com.fidan.floorplan.service;

import com.alibaba.fastjson.JSONObject;

import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;

public interface RequestService {

//    发送Get请求
    String get(String url, Map<String, String> params);

//    发送Post请求
    String post(String url, String json);

//    检查post数据中字段数据是否完整
    boolean checkPostParams(JSONObject data, List<String>params);

//    检查get数据中字段数据是否完整
    boolean checkGetParams(HttpServletRequest data, List<String>params);
}
