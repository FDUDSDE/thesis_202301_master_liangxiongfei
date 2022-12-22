package com.fidan.floorplan.service;

import com.alibaba.fastjson.JSONObject;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.List;
import java.util.Map;

@Service
public class RequestServiceImpl implements RequestService{

    Logger logger = LoggerFactory.getLogger(this.getClass());

    OkHttpClient okHttpClient = new OkHttpClient();

    public static final MediaType JSON
            = MediaType.get("application/json; charset=utf-8");

    @Override
    public String get(String url, Map<String, String> params) {
        HttpUrl.Builder httpBuilder = HttpUrl.parse(url).newBuilder();

        if(params != null){
            for(Map.Entry<String, String> param: params.entrySet()){
                httpBuilder.addQueryParameter(param.getKey(),param.getValue());
            }
        }
        logger.info("Get: "+httpBuilder.build());

        Request request = new Request.Builder()
                .url(httpBuilder.build())
                .get()
                .build();

        try {

            Response response = okHttpClient.newCall(request).execute();
            if(response.isSuccessful())
                return response.body().string();
        }catch (Exception e){
            e.printStackTrace();
        }
        return null;
    }

    @Override
    public String post(String url, String json) {
        RequestBody body = RequestBody.create(JSON, json);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        logger.info("Post："+url);

        try (Response response = okHttpClient.newCall(request).execute()) {

            return response.body().string();

        } catch (IOException e) {

            e.printStackTrace();

        }
        return null;
    }

    @Override
    public boolean checkPostParams(JSONObject data, List<String> params) {
        for(String param:params)
            if(data.get(param)==null)
                return false;
        return true;
    }

    @Override
    public boolean checkGetParams(HttpServletRequest data, List<String> params) {
        for(String param:params)
            if(data.getParameter(param)==null)
                return false;
        return true;
    }
}
