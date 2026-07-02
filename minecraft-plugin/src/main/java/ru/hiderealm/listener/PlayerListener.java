package ru.hiderealm.listener;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.scheduler.BukkitTask;
import ru.hiderealm.HideRealmPlugin;
import ru.hiderealm.bot.BotAPIClient;
import ru.hiderealm.util.IPGeolocator;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class PlayerListener implements Listener {

    private final HideRealmPlugin plugin;
    private final BotAPIClient bot;
    private final IPGeolocator geo;
    private final Map<UUID, BukkitTask> loginPolls = new ConcurrentHashMap<>();

    private static final Component PREFIX = Component.text()
            .append(Component.text("HideRealm ", NamedTextColor.GOLD))
            .append(Component.text(">> ", NamedTextColor.GRAY))
            .build();

    public PlayerListener(HideRealmPlugin plugin) {
        this.plugin = plugin;
        this.bot = plugin.getBotClient();
        this.geo = plugin.getGeolocator();
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        UUID uuid = player.getUniqueId();
        String ip = Objects.requireNonNull(player.getAddress()).getAddress().getHostAddress();

        new BukkitRunnable() {
            @Override
            public void run() {
                try {
                    IPGeolocator.GeoInfo geoInfo = geo.locate(ip);
                    BotAPIClient.JoinResult result = bot.sendPlayerJoin(
                            uuid, player.getName(), ip,
                            geoInfo != null ? geoInfo.city() : "",
                            geoInfo != null ? geoInfo.country() : "");

                    if (result == null) return;

                    if ("pending".equals(result.action())) {
                        BukkitTask pollTask = new BukkitRunnable() {
                            int elapsed = 0;
                            final int timeout = plugin.getConfig().getInt("login-timeout", 30);

                            @Override
                            public void run() {
                                elapsed++;
                                if (elapsed > timeout) {
                                    player.kick(Component.text("Время подтверждения истекло.", NamedTextColor.RED));
                                    loginPolls.remove(uuid);
                                    this.cancel();
                                    return;
                                }
                                try {
                                    String status = bot.checkLoginStatus(result.loginId());
                                    if ("approved".equals(status)) {
                                        player.sendMessage(PREFIX.append(
                                                Component.text("Вход подтвержден!", NamedTextColor.GREEN)));
                                        loginPolls.remove(uuid);
                                        this.cancel();
                                    } else if ("kicked".equals(status)) {
                                        player.kick(Component.text("Вы были кикнуты с сервера", NamedTextColor.RED));
                                        loginPolls.remove(uuid);
                                        this.cancel();
                                    } else if ("banned".equals(status)) {
                                        player.kick(Component.text("Аккаунт заблокирован", NamedTextColor.RED, TextDecoration.BOLD));
                                        loginPolls.remove(uuid);
                                        this.cancel();
                                    }
                                } catch (Exception e) {
                                    plugin.getLogger().warning("Login poll error: " + e.getMessage());
                                }
                            }
                        }.runTaskTimerAsynchronously(plugin, 20L, 20L);
                        loginPolls.put(uuid, pollTask);
                    }
                } catch (Exception e) {
                    plugin.getLogger().warning("Join API error: " + e.getMessage());
                }
            }
        }.runTaskAsynchronously(plugin);

        new BukkitRunnable() {
            @Override
            public void run() {
                checkPendingActions(player);
            }
        }.runTaskLaterAsynchronously(plugin, 100L);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        Player player = event.getPlayer();
        UUID uuid = player.getUniqueId();

        BukkitTask pollTask = loginPolls.remove(uuid);
        if (pollTask != null) {
            pollTask.cancel();
        }

        new BukkitRunnable() {
            @Override
            public void run() {
                try {
                    bot.sendPlayerLeave(uuid);
                } catch (Exception e) {
                    plugin.getLogger().warning("Leave API error: " + e.getMessage());
                }
            }
        }.runTaskAsynchronously(plugin);
    }

    public void checkPendingActions(Player player) {
        if (player == null || !player.isOnline()) return;

        try {
            List<BotAPIClient.PendingAction> actions = bot.getPendingActions();
            for (BotAPIClient.PendingAction action : actions) {
                if (!action.uuid().equals(player.getUniqueId().toString())) continue;

                switch (action.type()) {
                    case "kick" -> {
                        new BukkitRunnable() {
                            @Override
                            public void run() {
                                player.kick(Component.text("Вы были кикнуты с сервера", NamedTextColor.RED));
                                try { bot.completeAction(action.id()); } catch (Exception ignored) {}
                            }
                        }.runTask(plugin);
                    }
                    case "ban" -> {
                        new BukkitRunnable() {
                            @Override
                            public void run() {
                                player.kick(Component.text("Вы были кикнуты с сервера", NamedTextColor.RED));
                                try { bot.completeAction(action.id()); } catch (Exception ignored) {}
                            }
                        }.runTask(plugin);
                    }
                    case "restore" -> {
                        String password = action.params().getOrDefault("password", "");
                        if (!password.isEmpty()) {
                            String cmd = plugin.getConfig()
                                    .getString("password-reset-command", "authme changepassword %player% %password%")
                                    .replace("%player%", player.getName())
                                    .replace("%password%", password);
                            String finalCmd = cmd;
                            new BukkitRunnable() {
                                @Override
                                public void run() {
                                    plugin.getServer().dispatchCommand(
                                            plugin.getServer().getConsoleSender(), finalCmd);
                                    player.kick(Component.text("Вы были кикнуты с сервера", NamedTextColor.RED));
                                    try { bot.completeAction(action.id()); } catch (Exception ignored) {}
                                }
                            }.runTask(plugin);
                        }
                    }
                }
            }
        } catch (Exception e) {
            plugin.getLogger().warning("Check pending actions error: " + e.getMessage());
        }
    }

    public void startActionPolling() {
        new BukkitRunnable() {
            @Override
            public void run() {
                for (Player player : plugin.getServer().getOnlinePlayers()) {
                    checkPendingActions(player);
                }
            }
        }.runTaskTimerAsynchronously(plugin, 200L, 60L);
    }
}
