package ru.hiderealm;

import org.bukkit.plugin.java.JavaPlugin;
import ru.hiderealm.bot.BotAPIClient;
import ru.hiderealm.command.LinkCommand;
import ru.hiderealm.command.UnlinkCommand;
import ru.hiderealm.command.ChangePasswordCommand;
import ru.hiderealm.listener.PlayerListener;
import ru.hiderealm.util.IPGeolocator;

public class HideRealmPlugin extends JavaPlugin {

    private static HideRealmPlugin instance;
    private BotAPIClient botClient;
    private IPGeolocator geolocator;

    @Override
    public void onEnable() {
        instance = this;
        saveDefaultConfig();

        String apiUrl = getConfig().getString("bot-api-url", "http://localhost:5000");
        botClient = new BotAPIClient(apiUrl);
        geolocator = new IPGeolocator();

        getCommand("link").setExecutor(new LinkCommand(this));
        getCommand("unlink").setExecutor(new UnlinkCommand(this));
        getCommand("cp").setExecutor(new ChangePasswordCommand(this));

        PlayerListener listener = new PlayerListener(this);
        getServer().getPluginManager().registerEvents(listener, this);
        listener.startActionPolling();

        getLogger().info("HideRealmTG2FA enabled");
    }

    @Override
    public void onDisable() {
        getLogger().info("HideRealmTG2FA disabled");
    }

    public static HideRealmPlugin getInstance() {
        return instance;
    }

    public BotAPIClient getBotClient() {
        return botClient;
    }

    public IPGeolocator getGeolocator() {
        return geolocator;
    }
}
