package br.com.diarioescolarpro.data;

import android.os.Handler;
import android.os.Looper;
import br.com.diarioescolarpro.BuildConfig;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

public final class ApiClient {
    public interface Callback { void onResult(int status, JSONObject body, Exception error); }
    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(3);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private static String baseUrl() {
        String base = BuildConfig.API_BASE_URL;
        return base.endsWith("/") ? base : base + "/";
    }

    public static void get(String path, String token, Callback callback) { request("GET", path, token, null, callback); }
    public static void post(String path, String token, JSONObject body, Callback callback) { request("POST", path, token, body, callback); }

    public static void request(String method, String path, String token, JSONObject body, Callback callback) {
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            int status = 0;
            JSONObject response = null;
            Exception failure = null;
            try {
                connection = (HttpURLConnection) new URL(baseUrl() + path).openConnection();
                connection.setRequestMethod(method);
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(18000);
                connection.setRequestProperty("Accept", "application/json");
                if (token != null && !token.isEmpty()) connection.setRequestProperty("Authorization", "Bearer " + token);
                if (body != null) {
                    connection.setDoOutput(true);
                    connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                    try (OutputStream out = connection.getOutputStream()) { out.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
                }
                status = connection.getResponseCode();
                InputStream stream = status >= 400 ? connection.getErrorStream() : connection.getInputStream();
                StringBuilder text = new StringBuilder();
                if (stream != null) try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                    String line; while ((line = reader.readLine()) != null) text.append(line);
                }
                response = text.length() > 0 ? new JSONObject(text.toString()) : new JSONObject();
            } catch (Exception e) { failure = e; }
            finally { if (connection != null) connection.disconnect(); }
            int finalStatus = status; JSONObject finalResponse = response; Exception finalFailure = failure;
            MAIN.post(() -> callback.onResult(finalStatus, finalResponse, finalFailure));
        });
    }
}
