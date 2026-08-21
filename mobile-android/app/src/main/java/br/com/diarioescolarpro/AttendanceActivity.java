package br.com.diarioescolarpro;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import br.com.diarioescolarpro.data.ApiClient;
import br.com.diarioescolarpro.data.OfflineQueue;
import br.com.diarioescolarpro.security.SecureStore;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

public class AttendanceActivity extends Activity {
    private String token; private JSONObject schedule; private LinearLayout container; private ProgressBar progress; private TextView status;
    private SecureStore store;
    private EditText content, notes; private final ArrayList<StudentRow> rows = new ArrayList<>();

    static class StudentRow { int id; Spinner spinner; StudentRow(int id, Spinner spinner){this.id=id;this.spinner=spinner;} }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state); setContentView(R.layout.activity_attendance);
        store = new SecureStore(this); token = store.get("token");
        try { schedule = new JSONObject(getIntent().getStringExtra("schedule")); } catch (Exception e) { finish(); return; }
        container=findViewById(R.id.studentsContainer); progress=findViewById(R.id.progress); status=findViewById(R.id.status); content=findViewById(R.id.content); notes=findViewById(R.id.notes);
        JSONObject turma=schedule.optJSONObject("turma"), disc=schedule.optJSONObject("disciplina");
        ((TextView)findViewById(R.id.title)).setText((disc!=null?disc.optString("nome"):"Aula") + " · " + (turma!=null?turma.optString("nome"):""));
        ((TextView)findViewById(R.id.meta)).setText(schedule.optString("dia_semana_label") + " · " + schedule.optString("hora_inicio") + "–" + schedule.optString("hora_fim"));
        ((Button)findViewById(R.id.saveButton)).setOnClickListener(v -> save());
        loadStudents();
    }

    private void loadStudents(){
        JSONObject turma=schedule.optJSONObject("turma"); if(turma==null)return; progress.setVisibility(View.VISIBLE);
        ApiClient.get("api/v1/professor/turmas/"+turma.optInt("id")+"/alunos/",token,(code,body,error)->{
            progress.setVisibility(View.GONE); if(error!=null||code!=200||body==null){
                if (!loadStudentsFromCache(turma.optInt("id"))) status.setText("Não foi possível carregar os alunos. Conecte-se uma vez para sincronizar a turma.");
                else status.setText("Modo offline · lista de alunos sincronizada anteriormente.");
                return;
            }
            JSONArray items=body.optJSONArray("items"); container.removeAllViews(); rows.clear();
            if(items!=null) for(int i=0;i<items.length();i++){JSONObject a=items.optJSONObject(i);if(a!=null)addStudent(a);}
        });
    }


    private boolean loadStudentsFromCache(int turmaId) {
        try {
            String raw = store.get("bootstrap");
            if (raw == null) return false;
            JSONArray items = new JSONObject(raw).optJSONArray("alunos");
            if (items == null) return false;
            container.removeAllViews(); rows.clear();
            for (int i = 0; i < items.length(); i++) {
                JSONObject aluno = items.optJSONObject(i);
                if (aluno != null && aluno.optInt("turma_id") == turmaId) addStudent(aluno);
            }
            return !rows.isEmpty();
        } catch (Exception ignored) { return false; }
    }

    private void addStudent(JSONObject student){
        LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.HORIZONTAL); row.setPadding(8,12,8,12);
        TextView name=new TextView(this); name.setText(student.optString("nome")); name.setTextSize(16); name.setLayoutParams(new LinearLayout.LayoutParams(0,LinearLayout.LayoutParams.WRAP_CONTENT,1));
        Spinner spinner=new Spinner(this); String[] opts={"P","F","FJ"}; spinner.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,opts));
        row.addView(name);row.addView(spinner);container.addView(row);rows.add(new StudentRow(student.optInt("id"),spinner));
    }

    private void save(){
        try{
            JSONObject turma=schedule.getJSONObject("turma"),disc=schedule.getJSONObject("disciplina"); JSONArray freq=new JSONArray();
            for(StudentRow row:rows) freq.put(new JSONObject().put("aluno_id",row.id).put("status",row.spinner.getSelectedItem().toString()));
            JSONObject payload=new JSONObject()
                    .put("turma_id",turma.getInt("id")).put("disciplina_id",disc.getInt("id")).put("horario_id",schedule.getInt("id"))
                    .put("aula_numero",schedule.optInt("ordem",1)).put("data",new SimpleDateFormat("yyyy-MM-dd",Locale.US).format(new Date()))
                    .put("conteudo",content.getText().toString().trim()).put("observacoes",notes.getText().toString().trim()).put("quantidade_aulas",1).put("frequencias",freq);
            progress.setVisibility(View.VISIBLE); status.setText("Salvando…");
            ApiClient.post("api/v1/professor/aulas/registrar/",token,payload,(code,body,error)->{
                progress.setVisibility(View.GONE);
                if(error==null&&code==200){status.setText("Aula salva e sincronizada.");}
                else if(code==401){status.setText("Sua sessão expirou. Entre novamente pelo aplicativo.");}
                else {new OfflineQueue(this).add(payload);status.setText("Sem conexão. Aula protegida no aparelho e aguardando sincronização.");}
            });
        }catch(Exception e){status.setText("Não foi possível preparar o lançamento.");}
    }
}
