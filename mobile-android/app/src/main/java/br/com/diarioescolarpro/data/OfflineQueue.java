package br.com.diarioescolarpro.data;

import android.content.Context;
import br.com.diarioescolarpro.security.SecureStore;
import org.json.JSONArray;
import org.json.JSONObject;

public final class OfflineQueue {
    private static final String KEY = "pending_lessons";
    private final SecureStore store;
    public OfflineQueue(Context context) { store = new SecureStore(context); }

    public synchronized void add(JSONObject payload) {
        JSONArray arr = all();
        arr.put(payload);
        store.put(KEY, arr.toString());
    }
    public synchronized JSONArray all() {
        try { String raw = store.get(KEY); return raw == null ? new JSONArray() : new JSONArray(raw); }
        catch (Exception ignored) { return new JSONArray(); }
    }
    public synchronized int size() { return all().length(); }
    public synchronized void replace(JSONArray arr) { store.put(KEY, arr.toString()); }
    public synchronized void clear() { store.remove(KEY); }
}
