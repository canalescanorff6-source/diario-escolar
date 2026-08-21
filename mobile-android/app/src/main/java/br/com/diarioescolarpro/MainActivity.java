package br.com.diarioescolarpro;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;
import br.com.diarioescolarpro.data.ApiClient;
import br.com.diarioescolarpro.data.OfflineQueue;
import br.com.diarioescolarpro.security.SecureStore;
import java.util.ArrayList;
import java.util.Calendar;
import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private SecureStore store; private OfflineQueue queue; private String token;
    private final ArrayList<JSONObject> lessons = new ArrayList<>();
    private final ArrayList<String> labels = new ArrayList<>();
    private ArrayAdapter<String> adapter; private TextView syncStatus; private ProgressBar progress;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state); setContentView(R.layout.activity_main);
        store = new SecureStore(this); queue = new OfflineQueue(this); token = store.get("token");
        if (token == null) { goLogin(); return; }
        syncStatus = findViewById(R.id.syncStatus); progress = findViewById(R.id.progress);
        ListView list = findViewById(R.id.lessonsList); adapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, labels); list.setAdapter(adapter);
        list.setOnItemClickListener((parent, view, position, id) -> {
            if (position >= 0 && position < lessons.size()) openLesson(lessons.get(position));
        });
        ((Button)findViewById(R.id.logoutButton)).setOnClickListener(v -> ApiClient.post("api/v1/auth/logout/", token, new JSONObject(), (s,j,e) -> { store.clear(); queue.clear(); goLogin(); }));
        retryQueue(); refreshBootstrap(); loadLessons();
    }

    @Override protected void onResume() { super.onResume(); if (token != null) { updateSyncLabel(); loadLessons(); } }

    private void loadLessons() {
        progress.setVisibility(View.VISIBLE);
        ApiClient.get("api/v1/professor/aulas-hoje/", token, (status, body, error) -> {
            progress.setVisibility(View.GONE);
            if (status == 401) { store.clear(); goLogin(); return; }
            if (error != null || status != 200 || body == null) {
                if (!loadLessonsFromCache()) syncStatus.setText("Sem conexão e sem agenda local disponível. Conecte-se uma vez para sincronizar.");
                return;
            }
            lessons.clear(); labels.clear(); JSONArray arr = body.optJSONArray("items");
            if (arr != null) for (int i=0;i<arr.length();i++) {
                JSONObject item=arr.optJSONObject(i); if(item==null) continue; lessons.add(item);
                JSONObject turma=item.optJSONObject("turma"), disc=item.optJSONObject("disciplina");
                labels.add(item.optString("hora_inicio") + "  ·  " + (disc!=null?disc.optString("nome"):"") + "\n" + (turma!=null?turma.optString("nome"):""));
            }
            if (labels.isEmpty()) labels.add("Nenhuma aula prevista para hoje.");
            adapter.notifyDataSetChanged(); updateSyncLabel();
        });
    }


    private void refreshBootstrap() {
        ApiClient.get("api/v1/professor/bootstrap/", token, (status, body, error) -> {
            if (error == null && status == 200 && body != null) store.put("bootstrap", body.toString());
        });
    }

    private int modelDayOfWeek() {
        int day = Calendar.getInstance().get(Calendar.DAY_OF_WEEK);
        if (day == Calendar.SUNDAY) return 7;
        return day - 1; // Calendar: seg=2; modelo: seg=1.
    }

    private boolean loadLessonsFromCache() {
        try {
            String raw = store.get("bootstrap");
            if (raw == null) return false;
            JSONArray arr = new JSONObject(raw).optJSONArray("horarios");
            if (arr == null) return false;
            lessons.clear(); labels.clear();
            int today = modelDayOfWeek();
            for (int i = 0; i < arr.length(); i++) {
                JSONObject item = arr.optJSONObject(i);
                if (item == null || item.optInt("dia_semana") != today) continue;
                lessons.add(item);
                JSONObject turma = item.optJSONObject("turma"), disc = item.optJSONObject("disciplina");
                labels.add(item.optString("hora_inicio") + "  ·  " + (disc != null ? disc.optString("nome") : "") + "\n" + (turma != null ? turma.optString("nome") : ""));
            }
            if (labels.isEmpty()) labels.add("Nenhuma aula prevista para hoje.");
            adapter.notifyDataSetChanged();
            syncStatus.setText("Modo offline · usando agenda sincronizada anteriormente");
            return true;
        } catch (Exception ignored) { return false; }
    }

    private void openLesson(JSONObject item) {
        if (!item.has("id")) return;
        Intent intent = new Intent(this, AttendanceActivity.class);
        intent.putExtra("schedule", item.toString()); startActivity(intent);
    }

    private void retryQueue() {
        JSONArray pending = queue.all(); if (pending.length()==0) { updateSyncLabel(); return; }
        JSONObject first = pending.optJSONObject(0); if(first==null){queue.clear();return;}
        ApiClient.post("api/v1/professor/aulas/registrar/", token, first, (status, body, error) -> {
            if (error==null && status==200) {
                JSONArray remaining=new JSONArray(); for(int i=1;i<pending.length();i++) remaining.put(pending.opt(i)); queue.replace(remaining); retryQueue();
            } else updateSyncLabel();
        });
    }
    private void updateSyncLabel(){ int n=queue.size(); syncStatus.setText(n==0?"Tudo sincronizado":n+" lançamento(s) aguardando sincronização"); }
    private void goLogin(){ startActivity(new Intent(this, LoginActivity.class)); finish(); }
}
