package br.com.diarioescolarpro;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import br.com.diarioescolarpro.data.ApiClient;
import br.com.diarioescolarpro.security.SecureStore;
import org.json.JSONObject;

public class LoginActivity extends Activity {
    private SecureStore store;
    private ProgressBar progress;
    private TextView error;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state); setContentView(R.layout.activity_login);
        store = new SecureStore(this);
        if (store.get("token") != null) { openMain(); return; }
        EditText username = findViewById(R.id.username), password = findViewById(R.id.password);
        progress = findViewById(R.id.progress); error = findViewById(R.id.error);
        Button button = findViewById(R.id.loginButton);
        button.setOnClickListener(v -> {
            String user = username.getText().toString().trim(), pass = password.getText().toString();
            if (user.isEmpty() || pass.isEmpty()) { showError("Informe usuário e senha."); return; }
            button.setEnabled(false); progress.setVisibility(View.VISIBLE); error.setVisibility(View.GONE);
            try {
                JSONObject body = new JSONObject().put("username", user).put("password", pass);
                ApiClient.post("api/v1/auth/login/", null, body, (status, json, exception) -> {
                    button.setEnabled(true); progress.setVisibility(View.GONE);
                    if (exception != null) { showError("Não foi possível conectar ao servidor."); return; }
                    if (status != 200 || json == null || !json.optBoolean("ok")) { showError(json != null ? json.optString("message", "Acesso negado.") : "Acesso negado."); return; }
                    try { store.put("token", json.getString("token")); openMain(); } catch (Exception e) { showError("Não foi possível salvar a sessão com segurança."); }
                });
            } catch (Exception e) { button.setEnabled(true); progress.setVisibility(View.GONE); showError("Dados inválidos."); }
        });
    }
    private void showError(String message) { error.setText(message); error.setVisibility(View.VISIBLE); }
    private void openMain() { startActivity(new Intent(this, MainActivity.class)); finish(); }
}
