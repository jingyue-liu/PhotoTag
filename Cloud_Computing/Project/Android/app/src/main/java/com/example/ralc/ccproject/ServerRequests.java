package com.example.ralc.ccproject;

import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Base64;
import android.util.Log;
import android.widget.EditText;

import com.loopj.android.http.AsyncHttpClient;
import com.loopj.android.http.AsyncHttpResponseHandler;
import com.loopj.android.http.JsonHttpResponseHandler;
import com.loopj.android.http.RequestParams;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.util.Iterator;

import cz.msebera.android.httpclient.Header;
/**
 * Created by ralc on 5/9/17.
 */

public class ServerRequests {
    private static final int CONNECTION_TIMEOUT = 1000 * 5;
    private static final int MAX_RETRY = 0;
    private static final String SERVER_ADDRESS = "http://ec2-34-203-199-217.compute-1.amazonaws.com:5000";
    private static final String TAG = "ServerRequests";
    private Context context;
    private ProgressDialog progressDialog;

    public ServerRequests(Context context){
        progressDialog = new ProgressDialog(context);
        progressDialog.setCancelable(false);
        progressDialog.setTitle("Processing");
        progressDialog.setMessage("Please wait...");
        this.context = context;
    }

    public void uploadImage(Bitmap image, String name, final GetUserCallback callback){
        progressDialog.show();
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        image.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream);
        String encodedImage = Base64.encodeToString(byteArrayOutputStream.toByteArray(), Base64.DEFAULT);

        AsyncHttpClient client = new AsyncHttpClient();
        client.setMaxRetriesAndTimeout(MAX_RETRY, CONNECTION_TIMEOUT);
        RequestParams params = new RequestParams();
        JSONObject overall = new JSONObject();
        try{
            overall.put("name",name);
            overall.put("image", encodedImage);
        }catch (Exception e) {
            e.printStackTrace();
            showError();
        }
        params.add("payload", overall.toString());
        //params.add("image", encodedImage.toString());
        client.post(SERVER_ADDRESS+"/test", params, new JsonHttpResponseHandler(){
            @Override
            public void onSuccess(int statusCode, Header[] headers, JSONObject response){
                try {
                    GetUserCallback userCallback = callback;
                    progressDialog.dismiss();
                    userCallback.flagged(response.getBoolean("Status"));
                } catch(Exception e){
                    progressDialog.dismiss();
                    Log.e(TAG, "JSON parse error while registering");
                    showError();
                }
            }

            @Override
            public void onFailure(int statusCode, Header[] header, Throwable throwable, JSONObject
                                  errorResponse) {
                progressDialog.dismiss();
                Log.e(TAG, "Upload Success");
                showError();
            }
        });

    }

    public void fetchImage(String in, final GetUserCallback callback){
        progressDialog.show();

        AsyncHttpClient client = new AsyncHttpClient();
        client.setMaxRetriesAndTimeout(MAX_RETRY, CONNECTION_TIMEOUT);

        client.get(SERVER_ADDRESS + "/tags/" + in, new JsonHttpResponseHandler(){
            @Override
            public void onSuccess(int statusCode, Header[] headers, JSONObject response) {
                System.out.println(response.toString());
                String x = "";
                try {

                    Iterator<String> y = response.getJSONObject("imgs").keys();
                    while (y.hasNext()){
                        //System.out.println(y.next());
                        x = x + "," + response.getJSONObject("imgs").getString(y.next());
                    }

                } catch (JSONException e) {
                    e.printStackTrace();
                }

                GetUserCallback userCallback = callback;
                userCallback.imgData(x);
                progressDialog.dismiss();
                try {
                    userCallback.flagged(response.getBoolean("tags"));
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }

            @Override
            public void onFailure(int statusCode, Header[] headers, Throwable throwable, JSONObject
                                  errorResponse) {
                progressDialog.dismiss();
                Log.e(TAG, "Network Failure");
                showError();
            }
        });

    }

    private void showError() {
        AlertDialog.Builder dialogBuilder = new AlertDialog.Builder(context);
        dialogBuilder.setMessage("Upload Success.");
        dialogBuilder.setPositiveButton("OK", null);
        dialogBuilder.show();
    }

    private void showImageError() {
        AlertDialog.Builder dialogBuilder = new AlertDialog.Builder(context);
        dialogBuilder.setMessage("Image not found on server");
        dialogBuilder.setPositiveButton("OK", null);
        dialogBuilder.show();
    }
}
