package ru.hiderealm.command;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.entity.Player;
import org.bukkit.scheduler.BukkitRunnable;
import ru.hiderealm.HideRealmPlugin;
import ru.hiderealm.bot.BotAPIClient;

import java.util.*;

public class LinkCommand implements org.bukkit.command.CommandExecutor {

    private final HideRealmPlugin plugin;
    private final Map<UUID, Long> pendingLinks = new HashMap<>();
    private static final long LINK_TIMEOUT = 30000;

    private static final Component PREFIX = Component.text()
            .append(Component.text("HideRealm ", NamedTextColor.GOLD))
            .append(Component.text(">> ", NamedTextColor.GRAY))
            .build();

    public LinkCommand(HideRealmPlugin plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(org.bukkit.command.CommandSender sender, org.bukkit.command.Command command, String label, String[] args) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(Component.text("Only players can use this command."));
            return true;
        }

        Player player = (Player) sender;
        UUID uuid = player.getUniqueId();

        Long lastTime = pendingLinks.get(uuid);
        long now = System.currentTimeMillis();

        if (lastTime == null || (now - lastTime) > LINK_TIMEOUT) {
            pendingLinks.put(uuid, now);

            sender.sendMessage(PREFIX.append(Component.text("Внимание!", NamedTextColor.RED, TextDecoration.BOLD)));
            sender.sendMessage(PREFIX.append(Component.text("Вы собираетесь привязать аккаунт к: ", NamedTextColor.WHITE))
                    .append(Component.text("Telegram боту", NamedTextColor.GOLD)));
            sender.sendMessage(PREFIX.append(Component.text("Для продолжения введите команду еще раз!", NamedTextColor.WHITE)));
            sender.sendMessage(PREFIX.append(Component.text("Остерегайтесь мошенников!", NamedTextColor.RED, TextDecoration.BOLD)));
            sender.sendMessage(PREFIX.append(Component.text("Они могут украсть ваш аккаунт!", NamedTextColor.RED, TextDecoration.BOLD)));
            return true;
        }

        pendingLinks.remove(uuid);

        sender.sendMessage(PREFIX.append(Component.text("Генерирую код...", NamedTextColor.WHITE)));

        new BukkitRunnable() {
            @Override
            public void run() {
                try {
                    String code = plugin.getBotClient().createLinkCode(uuid, player.getName());
                    if (code != null) {
                        sender.sendMessage(PREFIX.append(Component.text("Ваш код: ", NamedTextColor.WHITE))
                                .append(Component.text(code, NamedTextColor.GOLD, TextDecoration.BOLD)));
                        sender.sendMessage(PREFIX.append(Component.text("Введите его в Telegram боте: /link " + code, NamedTextColor.WHITE)));
                    } else {
                        sender.sendMessage(PREFIX.append(Component.text("Ошибка при создании кода. Попробуйте позже.", NamedTextColor.RED)));
                    }
                } catch (Exception e) {
                    sender.sendMessage(PREFIX.append(Component.text("Ошибка связи с ботом.", NamedTextColor.RED)));
                    plugin.getLogger().warning("Link API error: " + e.getMessage());
                }
            }
        }.runTaskAsynchronously(plugin);

        new BukkitRunnable() {
            int tries = 0;

            @Override
            public void run() {
                tries++;
                if (tries > 30) {
                    this.cancel();
                    return;
                }
                try {
                    boolean confirmed = plugin.getBotClient().checkLinkConfirmed(uuid);
                    if (confirmed) {
                        sender.sendMessage(PREFIX.append(Component.text("Вы успешно привязали свой аккаунт", NamedTextColor.WHITE)));
                        this.cancel();
                    }
                } catch (Exception ignored) {
                }
            }
        }.runTaskTimerAsynchronously(plugin, 40L, 40L);

        return true;
    }
}
