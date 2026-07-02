package ru.hiderealm.util;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class IPGeolocator {

    private final HttpClient client;

    public IPGeolocator() {
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    public GeoInfo locate(String ip) {
        try {
            String url = "http://ip-api.com/json/" + ip + "?fields=city,country,query,status";
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            JsonObject json = JsonParser.parseString(resp.body()).getAsJsonObject();

            if ("success".equals(json.get("status").getAsString())) {
                String city = json.has("city") && !json.get("city").isJsonNull()
                        ? json.get("city").getAsString() : "";
                String country = json.has("country") && !json.get("country").isJsonNull()
                        ? json.get("country").getAsString() : "";
                return new GeoInfo(city, country);
            }
        } catch (Exception ignored) {
        }
        return new GeoInfo("", "");
    }

    public record GeoInfo(String city, String country) {
    }
}
