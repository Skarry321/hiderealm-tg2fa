package ru.hiderealm.bot;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

public class BotAPIClient {

    private final String baseUrl;
    private final HttpClient client;
    private final Gson gson;
    private final String serverId;

    public BotAPIClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
        this.gson = new Gson();
        this.serverId = "main";
    }

    public String createLinkCode(UUID uuid, String username) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("uuid", uuid.toString());
        body.addProperty("username", username);

        JsonObject resp = post("/api/link/create", body);
        if (resp != null && resp.has("code")) {
            return resp.get("code").getAsString();
        }
        return null;
    }

    public boolean checkLinkConfirmed(UUID uuid) throws Exception {
        String url = baseUrl + "/api/link/check?uuid=" + uuid;
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        JsonObject json = JsonParser.parseString(resp.body()).getAsJsonObject();
        return json.has("confirmed") && json.get("confirmed").getAsBoolean();
    }

    public boolean verifyLinkCode(UUID uuid, String username, String code) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("uuid", uuid.toString());
        body.addProperty("username", username);
        body.addProperty("code", code);

        JsonObject resp = post("/api/link/verify", body);
        if (resp != null && resp.has("success")) {
            return resp.get("success").getAsBoolean();
        }
        return false;
    }

    public JoinResult sendPlayerJoin(UUID uuid, String username, String ip, String city, String country) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("uuid", uuid.toString());
        body.addProperty("username", username);
        body.addProperty("ip", ip);
        body.addProperty("city", city);
        body.addProperty("country", country);

        JsonObject resp = post("/api/player/join", body);
        if (resp == null) return null;

        String action = resp.has("action") ? resp.get("action").getAsString() : "none";
        String loginId = resp.has("login_id") ? resp.get("login_id").getAsString() : "";
        String reason = resp.has("reason") ? resp.get("reason").getAsString() : "";
        return new JoinResult(action, loginId, reason);
    }

    public String checkLoginStatus(String loginId) throws Exception {
        String url = baseUrl + "/api/player/login-status?login_id=" + loginId;
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        JsonObject json = JsonParser.parseString(resp.body()).getAsJsonObject();
        return json.has("status") ? json.get("status").getAsString() : "expired";
    }

    public void sendPlayerLeave(UUID uuid) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("uuid", uuid.toString());
        post("/api/player/leave", body);
    }

    public List<PendingAction> getPendingActions() throws Exception {
        String url = baseUrl + "/api/actions/pending?server_id=" + serverId;
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        JsonObject json = JsonParser.parseString(resp.body()).getAsJsonObject();

        List<PendingAction> actions = new ArrayList<>();
        if (json.has("actions")) {
            for (JsonElement el : json.getAsJsonArray("actions")) {
                JsonObject obj = el.getAsJsonObject();
                String id = obj.get("id").getAsString();
                String type = obj.get("type").getAsString();
                String uuid = obj.get("uuid").getAsString();

                Map<String, String> params = new HashMap<>();
                if (obj.has("params") && obj.get("params").isJsonObject()) {
                    JsonObject pobj = obj.getAsJsonObject("params");
                    params = pobj.entrySet().stream()
                            .collect(Collectors.toMap(
                                    Map.Entry::getKey,
                                    e -> e.getValue().isJsonNull() ? "" : e.getValue().getAsString()));
                }
                actions.add(new PendingAction(id, type, uuid, params));
            }
        }
        return actions;
    }

    public void completeAction(String actionId) throws Exception {
        JsonObject body = new JsonObject();
        body.addProperty("action_id", actionId);
        post("/api/actions/complete", body);
    }

    private JsonObject post(String path, JsonObject body) throws Exception {
        HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .timeout(Duration.ofSeconds(5))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(body)))
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() >= 200 && resp.statusCode() < 300) {
            return JsonParser.parseString(resp.body()).getAsJsonObject();
        }
        return null;
    }

    public record JoinResult(String action, String loginId, String reason) {
    }

    public record PendingAction(String id, String type, String uuid, Map<String, String> params) {
    }
}
