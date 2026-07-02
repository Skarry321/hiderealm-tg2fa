package ru.hiderealm.command;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.entity.Player;
import org.bukkit.scheduler.BukkitRunnable;
import ru.hiderealm.HideRealmPlugin;

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
        if (!(sender instanceof Player player)) {
            sender.sendMessage(Component.text("Only players can use this command."));
            return true;
        }

        UUID uuid = player.getUniqueId();
        long now = System.currentTimeMillis();
        Long lastTime = pendingLinks.get(uuid);

        if (args.length > 0) {
            String code = args[0];
            new BukkitRunnable() {
                @Override
                public void run() {
                    try {
                        boolean success = plugin.getBotClient().verifyLinkCode(uuid, player.getName(), code);
                        if (success) {
                            sender.sendMessage(PREFIX.append(
                                    Component.text("Вы успешно привязали свой аккаунт", NamedTextColor.WHITE)));
                        } else {
                            sender.sendMessage(PREFIX.append(
                                    Component.text("Неверный или просроченный код! Попробуйте снова в Telegram боте.", NamedTextColor.RED)));
                        }
                    } catch (Exception e) {
                        sender.sendMessage(PREFIX.append(
                                Component.text("Ошибка связи с ботом.", NamedTextColor.RED)));
                        plugin.getLogger().warning("Link verify error: " + e.getMessage());
                    }
                }
            }.runTaskAsynchronously(plugin);
            return true;
        }

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

        sender.sendMessage(PREFIX.append(Component.text("Введите код из Telegram бота:", NamedTextColor.WHITE)));
        sender.sendMessage(PREFIX.append(Component.text("/link <код>", NamedTextColor.GOLD)));

        return true;
    }
}
